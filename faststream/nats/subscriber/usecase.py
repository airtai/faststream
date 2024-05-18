import asyncio
from abc import abstractmethod
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Union,
    cast,
)

import anyio
from fast_depends.dependencies import Depends
from nats.errors import ConnectionClosedError, TimeoutError
from typing_extensions import Annotated, Doc, override

from faststream.broker.message import StreamMessage
from faststream.broker.publisher.fake import FakePublisher
from faststream.broker.subscriber.usecase import SubscriberUsecase
from faststream.broker.types import CustomCallable, MsgType
from faststream.exceptions import NOT_CONNECTED_YET, SetupError
from faststream.nats.parser import BatchParser, JsParser, NatsParser
from faststream.nats.schemas.js_stream import compile_nats_wildcard
from faststream.types import AnyDict, LoggerProto, SendableMessage

if TYPE_CHECKING:
    from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
    from nats.aio.client import Client
    from nats.aio.msg import Msg
    from nats.aio.subscription import Subscription
    from nats.js import JetStreamContext

    from faststream.broker.message import StreamMessage
    from faststream.broker.publisher.proto import ProducerProto
    from faststream.broker.types import (
        AsyncCallable,
        BrokerMiddleware,
    )
    from faststream.nats.schemas import JStream, PullSub
    from faststream.types import Decorator


class LogicSubscriber(SubscriberUsecase[MsgType]):
    """A class to represent a NATS handler."""

    subscription: Union[
        None,
        "Subscription",
        "JetStreamContext.PushSubscription",
        "JetStreamContext.PullSubscription",
    ]
    producer: Optional["ProducerProto"]
    _connection: Union["Client", "JetStreamContext", None]

    def __init__(
        self,
        *,
        subject: str,
        extra_options: Optional[AnyDict],
        queue: str,
        stream: Optional["JStream"],
        pull_sub: Optional["PullSub"],
        # Subscriber args
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        no_ack: bool,
        retry: Union[bool, int],
        broker_dependencies: Iterable[Depends],
        broker_middlewares: Iterable["BrokerMiddleware[MsgType]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        _, path = compile_nats_wildcard(subject)

        self.subject = path
        self.queue = queue

        self.stream = stream
        self.pull_sub = pull_sub
        self.extra_options = extra_options or {}

        super().__init__(
            default_parser=default_parser,
            default_decoder=default_decoder,
            # Propagated args
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self._connection = None
        self.subscription = None
        self.producer = None
        self.tasks: List["asyncio.Task[Any]"] = []

    @override
    def setup(  # type: ignore[override]
        self,
        *,
        connection: Union["Client", "JetStreamContext"],
        # basic args
        logger: Optional["LoggerProto"],
        producer: Optional["ProducerProto"],
        graceful_timeout: Optional[float],
        extra_context: "AnyDict",
        # broker options
        broker_parser: Optional["CustomCallable"],
        broker_decoder: Optional["CustomCallable"],
        # dependant args
        apply_types: bool,
        is_validate: bool,
        _get_dependant: Optional[Callable[..., Any]],
        _call_decorators: Iterable["Decorator"],
    ) -> None:
        self._connection = connection

        super().setup(
            logger=logger,
            producer=producer,
            graceful_timeout=graceful_timeout,
            extra_context=extra_context,
            broker_parser=broker_parser,
            broker_decoder=broker_decoder,
            apply_types=apply_types,
            is_validate=is_validate,
            _get_dependant=_get_dependant,
            _call_decorators=_call_decorators,
        )

    async def start(self) -> None:
        """Create NATS subscription and start consume tasks."""
        assert self._connection, NOT_CONNECTED_YET  # nosec B101
        await super().start()
        await self._create_subscription(connection=self._connection)

    async def close(self) -> None:
        """Clean up handler subscription, cancel consume task in graceful mode."""
        await super().close()

        if self.subscription is not None:
            await self.subscription.unsubscribe()
            self.subscription = None

        for task in self.tasks:
            if not task.done():
                task.cancel()
        self.tasks = []

    @abstractmethod
    async def _create_subscription(
        self,
        *,
        connection: Union["Client", "JetStreamContext"],
    ) -> None:
        """Create NATS subscription object to consume messages."""
        raise NotImplementedError()

    def _make_response_publisher(
        self,
        message: Annotated[
            "StreamMessage[Any]",
            Doc("Message requiring reply"),
        ],
    ) -> Sequence[FakePublisher]:
        """Create FakePublisher object to use it as one of `publishers` in `self.consume` scope."""
        if not message.reply_to or self._producer is None:
            return ()

        return (
            FakePublisher(
                self._producer.publish,
                publish_kwargs={
                    "subject": message.reply_to,
                },
            ),
        )

    def __hash__(self) -> int:
        return self.get_routing_hash(self.subject)

    @staticmethod
    def get_routing_hash(
        subject: Annotated[
            str,
            Doc("NATS subject to consume messages"),
        ],
    ) -> int:
        """Get handler hash by outer data.

        Using to find handler in `broker.handlers` dictionary.
        """
        return hash(subject)

    @staticmethod
    def build_log_context(
        message: Annotated[
            Optional["StreamMessage[Any]"],
            Doc("Message which we are building context for"),
        ],
        subject: Annotated[
            str,
            Doc("NATS subject we are listening"),
        ],
        *,
        queue: Annotated[
            str,
            Doc("Using queue group name"),
        ] = "",
        stream: Annotated[
            Optional["JStream"],
            Doc("Stream object we are listening"),
        ] = None,
    ) -> Dict[str, str]:
        """Static method to build log context out of `self.consume` scope."""
        return {
            "subject": subject,
            "queue": queue,
            "stream": getattr(stream, "name", ""),
            "message_id": getattr(message, "message_id", ""),
        }

    def get_log_context(
        self,
        message: Annotated[
            Optional["StreamMessage[Any]"],
            Doc("Message which we are building context for"),
        ],
    ) -> Dict[str, str]:
        """Log context factory using in `self.consume` scope."""
        return self.build_log_context(
            message=message,
            subject=self.subject,
            queue=self.queue,
            stream=self.stream,
        )

    def add_prefix(self, prefix: str) -> None:
        """Include Subscriber in router."""
        self.subject = "".join((prefix, self.subject))


class DefaultHandler(LogicSubscriber["Msg"]):
    """One-message consumer class."""

    send_stream: "MemoryObjectSendStream[Msg]"
    receive_stream: "MemoryObjectReceiveStream[Msg]"

    def __init__(
        self,
        *,
        max_workers: int,
        # default args
        subject: str,
        queue: str,
        stream: Optional["JStream"],
        pull_sub: Optional["PullSub"],
        extra_options: Optional[AnyDict],
        # Subscriber args
        no_ack: bool,
        retry: Union[bool, int],
        broker_dependencies: Iterable[Depends],
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser_: Union[NatsParser, JsParser] = (
            NatsParser(pattern=subject) if stream is None else JsParser(pattern=subject)
        )

        super().__init__(
            subject=subject,
            queue=queue,
            stream=stream,
            pull_sub=pull_sub,
            extra_options=extra_options,
            # subscriber args
            default_parser=parser_.parse_message,
            default_decoder=parser_.decode_message,
            # Propagated args
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

        self.max_workers = max_workers

        self.send_stream, self.receive_stream = anyio.create_memory_object_stream(
            max_buffer_size=max_workers
        )
        self.limiter = anyio.Semaphore(max_workers)

    async def _create_subscription(
        self,
        *,
        connection: Union["Client", "JetStreamContext"],
    ) -> None:
        """Create NATS subscription and start consume task."""
        cb: Callable[["Msg"], Awaitable[Any]]
        if self.max_workers > 1:
            self.tasks.append(asyncio.create_task(self._serve_consume_queue()))
            cb = self.__put_msg
        else:
            cb = self.consume

        if self.pull_sub is not None:
            connection = cast("JetStreamContext", connection)

            if self.stream is None:
                raise SetupError("Pull subscriber can be used only with a stream")

            self.subscription = await connection.pull_subscribe(
                subject=self.subject,
                **self.extra_options,
            )
            self.tasks.append(asyncio.create_task(self._consume_pull(cb=cb)))

        else:
            self.subscription = await connection.subscribe(
                subject=self.subject,
                queue=self.queue,
                cb=cb,  # type: ignore[arg-type]
                **self.extra_options,
            )

    async def _serve_consume_queue(
        self,
    ) -> None:
        """Endless task consuming messages from in-memory queue.

        Suitable to batch messages by amount, timestamps, etc and call `consume` for this batches.
        """
        async with anyio.create_task_group() as tg:
            async for msg in self.receive_stream:
                tg.start_soon(self.__consume_msg, msg)

    async def _consume_pull(
        self,
        cb: Callable[["Msg"], Awaitable[SendableMessage]],
    ) -> None:
        """Endless task consuming messages using NATS Pull subscriber."""
        assert self.pull_sub  # nosec B101

        sub = cast("JetStreamContext.PullSubscription", self.subscription)

        while self.running:  # pragma: no branch
            messages = []
            with suppress(TimeoutError, ConnectionClosedError):
                messages = await sub.fetch(
                    batch=self.pull_sub.batch_size,
                    timeout=self.pull_sub.timeout,
                )

            if messages:
                async with anyio.create_task_group() as tg:
                    for msg in messages:
                        tg.start_soon(cb, msg)

    async def __consume_msg(
        self,
        msg: "Msg",
    ) -> None:
        """Proxy method to call `self.consume` with semaphore block."""
        async with self.limiter:
            await self.consume(msg)

    async def __put_msg(self, msg: "Msg") -> None:
        """Proxy method to put msg into in-memory queue with semaphore block."""
        async with self.limiter:
            await self.send_stream.send(msg)


class BatchHandler(LogicSubscriber[List["Msg"]]):
    """Batch-message consumer class."""

    pull_sub: "PullSub"
    stream: "JStream"

    def __init__(
        self,
        *,
        # default args
        subject: str,
        queue: str,
        stream: Optional["JStream"],
        pull_sub: Optional["PullSub"],
        extra_options: Optional[AnyDict],
        # Subscriber args
        no_ack: bool,
        retry: Union[bool, int],
        broker_dependencies: Iterable[Depends],
        broker_middlewares: Iterable["BrokerMiddleware[List[Msg]]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = BatchParser(pattern=subject)

        super().__init__(
            subject=subject,
            queue=queue,
            stream=stream,
            pull_sub=pull_sub,
            extra_options=extra_options,
            # subscriber args
            default_parser=parser.parse_batch,
            default_decoder=parser.decode_batch,
            # Propagated args
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def _create_subscription(  # type: ignore[override]
        self,
        *,
        connection: "JetStreamContext",
    ) -> None:
        """Create NATS subscription and start consume task."""
        self.subscription = await connection.pull_subscribe(
            subject=self.subject,
            **self.extra_options,
        )
        self.tasks.append(asyncio.create_task(self._consume_pull()))

    async def _consume_pull(self) -> None:
        """Endless task consuming messages using NATS Pull subscriber."""
        assert self.subscription, "You should call `create_subscription` at first."  # nosec B101

        sub = cast("JetStreamContext.PullSubscription", self.subscription)

        while self.running:  # pragma: no branch
            with suppress(TimeoutError, ConnectionClosedError):
                messages = await sub.fetch(
                    batch=self.pull_sub.batch_size,
                    timeout=self.pull_sub.timeout,
                )

                if messages:
                    await self.consume(messages)
