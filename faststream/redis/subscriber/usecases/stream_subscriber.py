import math
from collections.abc import Awaitable, Iterable, Sequence
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
)

from redis.exceptions import ResponseError
from typing_extensions import TypeAlias, override

from faststream._internal.subscriber.mixins import ConcurrentMixin
from faststream._internal.subscriber.utils import process_msg
from faststream.redis.message import (
    BatchStreamMessage,
    DefaultStreamMessage,
    RedisStreamMessage,
    UnifyRedisDict,
)
from faststream.redis.parser import (
    RedisBatchStreamParser,
    RedisStreamParser,
)
from faststream.redis.schemas import StreamSub

from .basic import LogicSubscriber

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant

    from faststream._internal.types import (
        AsyncCallable,
        BrokerMiddleware,
    )
    from faststream.message import StreamMessage as BrokerStreamMessage
    from faststream.middlewares import AckPolicy


TopicName: TypeAlias = bytes
Offset: TypeAlias = bytes


class _StreamHandlerMixin(LogicSubscriber):
    def __init__(
        self,
        *,
        stream: StreamSub,
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Sequence["BrokerMiddleware[UnifyRedisDict]"],
    ) -> None:
        super().__init__(
            default_parser=default_parser,
            default_decoder=default_decoder,
            # Propagated options
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
        )

        self.stream_sub = stream
        self.last_id = stream.last_id

    def get_log_context(
        self,
        message: Optional["BrokerStreamMessage[Any]"],
    ) -> dict[str, str]:
        return self.build_log_context(
            message=message,
            channel=self.stream_sub.name,
        )

    @override
    async def start(self) -> None:
        if self.tasks:
            return

        assert self._client, "You should setup subscriber at first."  # nosec B101

        client = self._client

        self.extra_watcher_options.update(
            redis=client,
            group=self.stream_sub.group,
        )

        stream = self.stream_sub

        read: Callable[
            [str],
            Awaitable[
                tuple[
                    tuple[
                        TopicName,
                        tuple[
                            tuple[
                                Offset,
                                dict[bytes, bytes],
                            ],
                            ...,
                        ],
                    ],
                    ...,
                ],
            ],
        ]

        if stream.group and stream.consumer:
            try:
                await client.xgroup_create(
                    name=stream.name,
                    id=self.last_id,
                    groupname=stream.group,
                    mkstream=True,
                )
            except ResponseError as e:
                if "already exists" not in str(e):
                    raise

            def read(
                _: str,
            ) -> Awaitable[
                tuple[
                    tuple[
                        TopicName,
                        tuple[
                            tuple[
                                Offset,
                                dict[bytes, bytes],
                            ],
                            ...,
                        ],
                    ],
                    ...,
                ],
            ]:
                return client.xreadgroup(
                    groupname=stream.group,
                    consumername=stream.consumer,
                    streams={stream.name: ">"},
                    count=stream.max_records,
                    block=stream.polling_interval,
                    noack=stream.no_ack,
                )

        else:

            def read(
                last_id: str,
            ) -> Awaitable[
                tuple[
                    tuple[
                        TopicName,
                        tuple[
                            tuple[
                                Offset,
                                dict[bytes, bytes],
                            ],
                            ...,
                        ],
                    ],
                    ...,
                ],
            ]:
                return client.xread(
                    {stream.name: last_id},
                    block=stream.polling_interval,
                    count=stream.max_records,
                )

        await super().start(read)

    @override
    async def get_one(
        self,
        *,
        timeout: float = 5.0,
    ) -> "Optional[RedisStreamMessage]":
        assert self._client, "You should start subscriber at first."  # nosec B101
        assert (  # nosec B101
            not self.calls
        ), "You can't use `get_one` method if subscriber has registered handlers."

        stream_message = await self._client.xread(
            {self.stream_sub.name: self.last_id},
            block=math.ceil(timeout * 1000),
            count=1,
        )

        if not stream_message:
            return None

        ((stream_name, ((message_id, raw_message),)),) = stream_message

        self.last_id = message_id.decode()

        redis_incoming_msg = DefaultStreamMessage(
            type="stream",
            channel=stream_name.decode(),
            message_ids=[message_id],
            data=raw_message,
        )

        context = self._state.get().di_state.context

        msg: RedisStreamMessage = await process_msg(  # type: ignore[assignment]
            msg=redis_incoming_msg,
            middlewares=(
                m(redis_incoming_msg, context=context) for m in self._broker_middlewares
            ),
            parser=self._parser,
            decoder=self._decoder,
        )
        return msg

    def add_prefix(self, prefix: str) -> None:
        new_stream = deepcopy(self.stream_sub)
        new_stream.name = f"{prefix}{new_stream.name}"
        self.stream_sub = new_stream


class StreamSubscriber(_StreamHandlerMixin):
    def __init__(
        self,
        *,
        stream: StreamSub,
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Sequence["BrokerMiddleware[UnifyRedisDict]"],
    ) -> None:
        parser = RedisStreamParser()
        super().__init__(
            stream=stream,
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
        )

    async def _get_msgs(
        self,
        read: Callable[
            [str],
            Awaitable[
                tuple[
                    tuple[
                        TopicName,
                        tuple[
                            tuple[
                                Offset,
                                dict[bytes, bytes],
                            ],
                            ...,
                        ],
                    ],
                    ...,
                ],
            ],
        ],
    ) -> None:
        for stream_name, msgs in await read(self.last_id):
            if msgs:
                self.last_id = msgs[-1][0].decode()

                for message_id, raw_msg in msgs:
                    msg = DefaultStreamMessage(
                        type="stream",
                        channel=stream_name.decode(),
                        message_ids=[message_id],
                        data=raw_msg,
                    )

                    await self.consume_one(msg)


class StreamBatchSubscriber(_StreamHandlerMixin):
    def __init__(
        self,
        *,
        stream: StreamSub,
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Sequence["BrokerMiddleware[UnifyRedisDict]"],
    ) -> None:
        parser = RedisBatchStreamParser()
        super().__init__(
            stream=stream,
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
        )

    async def _get_msgs(
        self,
        read: Callable[
            [str],
            Awaitable[
                tuple[tuple[bytes, tuple[tuple[bytes, dict[bytes, bytes]], ...]], ...],
            ],
        ],
    ) -> None:
        for stream_name, msgs in await read(self.last_id):
            if msgs:
                self.last_id = msgs[-1][0].decode()

                data: list[dict[bytes, bytes]] = []
                ids: list[bytes] = []
                for message_id, i in msgs:
                    data.append(i)
                    ids.append(message_id)

                msg = BatchStreamMessage(
                    type="bstream",
                    channel=stream_name.decode(),
                    data=data,
                    message_ids=ids,
                )

                await self.consume_one(msg)


class ConcurrentStreamSubscriber(
    ConcurrentMixin["BrokerStreamMessage"], StreamSubscriber
):
    def __init__(
        self,
        *,
        stream: StreamSub,
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Sequence["BrokerMiddleware[UnifyRedisDict]"],
        max_workers: int,
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            stream=stream,
            # Propagated options
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            max_workers=max_workers,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    async def start(self) -> None:
        await super().start()
        self.start_consume_task()

    async def consume_one(self, msg: "BrokerStreamMessage") -> None:
        await self._put_msg(msg)
