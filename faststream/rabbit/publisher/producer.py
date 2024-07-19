from contextlib import asynccontextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    AsyncGenerator,
    Optional,
    Tuple,
    Union,
    cast,
)

import anyio
from aio_pika.abc import AbstractIncomingMessage
from typing_extensions import override

from faststream.broker.publisher.proto import ProducerProto
from faststream.broker.utils import resolve_custom_func
from faststream.exceptions import WRONG_PUBLISH_ARGS
from faststream.rabbit.parser import AioPikaParser
from faststream.rabbit.schemas import RABBIT_REPLY, RabbitExchange
from faststream.utils.classes import Singleton
from faststream.utils.functions import (
    fake_context_yielding,
    timeout_scope,
)

if TYPE_CHECKING:
    import aiormq
    from aio_pika import IncomingMessage, RobustChannel
    from aio_pika.abc import DateType, HeadersType, TimeoutType
    from anyio.streams.memory import MemoryObjectReceiveStream

    from faststream.broker.types import (
        AsyncCallable,
        CustomCallable,
    )
    from faststream.rabbit.helpers.declarer import RabbitDeclarer
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.types import SendableMessage


class AioPikaFastProducer(ProducerProto):
    """A class for fast producing messages using aio-pika."""

    _decoder: "AsyncCallable"
    _parser: "AsyncCallable"

    def __init__(
        self,
        *,
        declarer: "RabbitDeclarer",
        parser: Optional["CustomCallable"],
        decoder: Optional["CustomCallable"],
    ) -> None:
        self.declarer = declarer
        self.rpc_manager = _RPCManager(declarer=declarer)

        default_parser = AioPikaParser()
        self._parser = resolve_custom_func(parser, default_parser.parse_message)
        self._decoder = resolve_custom_func(decoder, default_parser.decode_message)

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "AioPikaSendableMessage",
        exchange: Union["RabbitExchange", str, None] = None,
        *,
        correlation_id: str = "",
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: "TimeoutType" = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        persist: bool = False,
        reply_to: Optional[str] = None,
        headers: Optional["HeadersType"] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        priority: Optional[int] = None,
        expiration: Optional["DateType"] = None,
        message_id: Optional[str] = None,
        timestamp: Optional["DateType"] = None,
        message_type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> Optional[Any]:
        """Publish a message to a RabbitMQ queue."""
        context: AsyncContextManager[
            Union[
                Tuple[MemoryObjectReceiveStream[IncomingMessage], RobustChannel],
                Tuple[None, None],
            ]
        ]
        channel: Optional[RobustChannel]
        response_queue: Optional[MemoryObjectReceiveStream[IncomingMessage]]

        if rpc:
            if reply_to is not None:
                raise WRONG_PUBLISH_ARGS

            context = self.rpc_manager()
            reply_to = RABBIT_REPLY.name

        else:
            context = fake_context_yielding(with_yield=(None, None))

        async with context as (response_queue, channel):
            r = await self._publish(
                message=message,
                exchange=exchange,
                routing_key=routing_key,
                mandatory=mandatory,
                immediate=immediate,
                timeout=timeout,
                persist=persist,
                reply_to=reply_to,
                headers=headers,
                content_type=content_type,
                content_encoding=content_encoding,
                priority=priority,
                correlation_id=correlation_id,
                expiration=expiration,
                message_id=message_id,
                timestamp=timestamp,
                message_type=message_type,
                user_id=user_id,
                app_id=app_id,
                channel=channel,
            )

            if response_queue is None:
                return r

            else:
                msg: Optional[IncomingMessage] = None
                with timeout_scope(rpc_timeout, raise_timeout):
                    msg = await response_queue.receive()

                if msg:  # pragma: no branch
                    return await self._decoder(await self._parser(msg))

        return None

    async def _publish(
        self,
        message: "AioPikaSendableMessage",
        *,
        correlation_id: str,
        exchange: Union["RabbitExchange", str, None],
        routing_key: str,
        mandatory: bool,
        immediate: bool,
        timeout: "TimeoutType",
        persist: bool,
        reply_to: Optional[str],
        headers: Optional["HeadersType"],
        content_type: Optional[str],
        content_encoding: Optional[str],
        priority: Optional[int],
        expiration: Optional["DateType"],
        message_id: Optional[str],
        timestamp: Optional["DateType"],
        message_type: Optional[str],
        user_id: Optional[str],
        app_id: Optional[str],
        channel: Optional["RobustChannel"],
    ) -> Union["aiormq.abc.ConfirmationFrameType", "SendableMessage"]:
        """Publish a message to a RabbitMQ exchange."""
        message = AioPikaParser.encode_message(
            message=message,
            persist=persist,
            reply_to=reply_to,
            headers=headers,
            content_type=content_type,
            content_encoding=content_encoding,
            priority=priority,
            correlation_id=correlation_id,
            expiration=expiration,
            message_id=message_id,
            timestamp=timestamp,
            message_type=message_type,
            user_id=user_id,
            app_id=app_id,
        )

        exchange_obj = await self.declarer.declare_exchange(
            exchange=RabbitExchange.validate(exchange),
            passive=True,
            channel=channel,
        )

        return await exchange_obj.publish(
            message=message,
            routing_key=routing_key,
            mandatory=mandatory,
            immediate=immediate,
            timeout=timeout,
        )


class _RPCManager(Singleton):
    """A class that provides an RPC lock."""

    def __init__(self, declarer: "RabbitDeclarer") -> None:
        self.declarer = declarer

    @asynccontextmanager
    async def __call__(
        self,
    ) -> AsyncGenerator[
        Tuple[
            "MemoryObjectReceiveStream[IncomingMessage]",
            "RobustChannel",
        ],
        None,
    ]:
        # NOTE: this allows us to make sure the channel is only used by a single
        # RPC call at a time, however, if the channel pool is used for both consuming
        # and producing, they will be blocked by each other
        async with self.declarer.declare_queue_scope(RABBIT_REPLY) as queue:
            consumer_tag = None
            try:
                (
                    send_response_stream,
                    receive_response_stream,
                ) = anyio.create_memory_object_stream[AbstractIncomingMessage](
                    max_buffer_size=1
                )
                consumer_tag = await queue.consume(
                    callback=send_response_stream.send,  # type: ignore[arg-type]
                    no_ack=True,
                )
                yield (
                    cast(
                        "MemoryObjectReceiveStream[IncomingMessage]",
                        receive_response_stream,
                    ),
                    cast("RobustChannel", queue.channel),
                )
            finally:
                if consumer_tag is not None:
                    await queue.cancel(consumer_tag)  # type: ignore[index]
