import asyncio
from abc import abstractmethod
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
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
from nats.errors import TimeoutError
from typing_extensions import Annotated, Doc, override

from faststream.broker.core.handler import BaseHandler
from faststream.broker.core.publisher import FakePublisher
from faststream.broker.parsers import resolve_custom_func
from faststream.broker.types import MsgType
from faststream.nats.parser import JsParser, Parser
from faststream.types import AnyDict, SendableMessage
from faststream.utils.path import compile_path

if TYPE_CHECKING:
    from anyio.abc import TaskGroup, TaskStatus
    from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
    from fast_depends.dependencies import Depends
    from nats.aio.client import Client
    from nats.aio.msg import Msg
    from nats.aio.subscription import Subscription
    from nats.js import JetStreamContext

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherProtocol,
        SubscriberMiddleware,
    )
    from faststream.nats.schemas import JStream, PullSub


class BaseNatsHandler(BaseHandler[MsgType]):
    """A class to represent a NATS handler."""

    subscription: Union[
        None,
        "Subscription",
        "JetStreamContext.PushSubscription",
        "JetStreamContext.PullSubscription",
    ]
    task_group: Optional["TaskGroup"]
    tasks: List["asyncio.Task[Any]"]
    send_stream: "MemoryObjectSendStream[Msg]"
    receive_stream: "MemoryObjectReceiveStream[Msg]"
    producer: Optional["PublisherProtocol"]

    def __init__(
        self,
        subject: Annotated[
            str,
            Doc("NATS subject to subscribe"),
        ],
        watcher: Annotated[
            Callable[..., AsyncContextManager[None]],
            Doc("Watcher to ack message"),
        ],
        extra_context: Annotated[
            Optional[AnyDict],
            Doc("Extra context to pass into consume scope"),
        ] = None,
        queue: Annotated[
            str,
            Doc("NATS queue name"),
        ] = "",
        stream: Annotated[
            Optional["JStream"],
            Doc("NATS Stream object"),
        ] = None,
        pull_sub: Annotated[
            Optional["PullSub"],
            Doc("NATS Pull consumer parameters container"),
        ] = None,
        extra_options: Annotated[
            Optional[AnyDict],
            Doc("Extra arguments for subscription creation"),
        ] = None,
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Wait up to this time (if set) in graceful shutdown mode. "
                "Kills task forcefully if expired."
            ),
        ] = None,
        max_workers: Annotated[
            int,
            Doc("Process up to this parameter messages concurrently"),
        ] = 1,
        middlewares: Annotated[
            Iterable["BrokerMiddleware[MsgType]"],
            Doc("Global middleware to use `on_receive`, `after_processed`"),
        ] = (),
        # AsyncAPI information
        description: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber description"),
        ] = None,
        title: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber title"),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whether to include the handler in AsyncAPI schema"),
        ] = True,
    ) -> None:
        """Initialize the NATS handler."""
        reg, path = compile_path(
            subject,
            replace_symbol="*",
            patch_regex=lambda x: x.replace(".>", "..+"),
        )
        self.subject = path
        self.path_regex = reg
        self.queue = queue

        self.stream = stream
        self.pull_sub = pull_sub
        self.extra_options = extra_options or {}

        super().__init__(
            description=description,
            include_in_schema=include_in_schema,
            title=title,
            middlewares=middlewares,
            graceful_timeout=graceful_timeout,
            watcher=watcher,
            extra_context=extra_context,
        )

        self.max_workers = max_workers
        self.subscription = None
        self.producer = None

        self.send_stream, self.receive_stream = anyio.create_memory_object_stream(
            max_buffer_size=max_workers
        )
        self.limiter = anyio.Semaphore(max_workers)
        self.tasks = []

    @override
    async def start(  # type: ignore[override]
        self,
        connection: Annotated[
            Union["Client", "JetStreamContext"],
            Doc("NATS client or JS Context object using to create subscription"),
        ],
        producer: Annotated[
            Optional["PublisherProtocol"],
            Doc("Publisher to response RPC"),
        ],
    ) -> None:
        """Create NATS subscription and start consume task."""
        self.producer = producer
        await self.create_subscription(connection)
        await super().start()

    @abstractmethod
    async def create_subscription(
        self,
        connection: Annotated[
            Union["Client", "JetStreamContext"],
            Doc("NATS client or JS Context object using to create subscription"),
        ],
    ) -> None:
        raise NotImplementedError()

    def make_response_publisher(
        self, message: "StreamMessage[Any]"
    ) -> Sequence[FakePublisher]:
        if not message.reply_to or self.producer is None:
            return ()

        return (
            FakePublisher(
                self.producer.publish,
                subject=message.reply_to,
            ),
        )

    async def close(self) -> None:
        """Clean up handler subscription, cancel consume task in graceful mode."""
        await super().close()

        if self.subscription is not None:
            await self.subscription.unsubscribe()
            self.subscription = None

        for t in self.tasks:
            t.cancel()
        self.tasks = []

    async def _consume_msg(
        self,
        msg: MsgType,
    ) -> None:
        """Proxy method to call `self.consume` with semaphore block."""
        async with self.limiter:
            await self.consume(msg)

    async def _put_msg(self, msg: "Msg") -> None:
        """Proxy method to put msg into in-memory queue with semaphore block."""
        async with self.limiter:
            await self.send_stream.send(msg)

    @staticmethod
    def get_routing_hash(
        subject: Annotated[str, Doc("NATS subject to consume messages")],
    ) -> str:
        """Get handler hash by outer data.

        Using to find handler in `broker.handlers` dictionary.
        """
        return subject

    @staticmethod
    def build_log_context(
        message: Optional["StreamMessage[Any]"],
        subject: str,
        queue: str = "",
        stream: Optional["JStream"] = None,
    ) -> Dict[str, str]:
        return {
            "subject": subject,
            "queue": queue,
            "stream": getattr(stream, "name", ""),
            "message_id": message.message_id if message else "",
        }

    def get_log_context(
        self,
        message: Optional["StreamMessage[Any]"],
    ) -> Dict[str, str]:
        return self.build_log_context(
            message=message,
            subject=self.subject,
            queue=self.queue,
            stream=self.stream,
        )


class DefaultHandler(BaseNatsHandler["Msg"]):
    """One-message consumer class."""

    @override
    def add_call(  # type: ignore[override]
        self,
        *,
        filter: "Filter[StreamMessage[Msg]]",
        parser: Optional["CustomParser[Msg]"],
        decoder: Optional["CustomDecoder[StreamMessage[Msg]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[Msg]":
        parser_ = Parser if self.stream is None else JsParser
        return super().add_call(
            parser_=resolve_custom_func(parser, parser_.parse_message),
            decoder_=resolve_custom_func(decoder, parser_.decode_message),
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    async def create_subscription(
        self,
        connection: Annotated[
            Union["Client", "JetStreamContext"],
            Doc("NATS client or JS Context object using to create subscription"),
        ],
    ) -> None:
        """Create NATS subscription and start consume task."""
        cb: Callable[["Msg"], Awaitable[SendableMessage]]
        if self.max_workers > 1:
            self.tasks.append(asyncio.create_task(self._serve_consume_queue()))
            cb = self._put_msg
        else:
            cb = self.consume

        if self.pull_sub is not None:
            connection = cast("JetStreamContext", connection)

            if self.stream is None:
                raise ValueError("Pull subscriber can be used only with a stream")

            self.subscription = await connection.pull_subscribe(
                subject=self.subject,
                **self.extra_options,
            )
            self.tasks.append(asyncio.create_task(self._consume_pull(cb)))

        else:
            self.subscription = await connection.subscribe(
                subject=self.subject,
                queue=self.queue,
                cb=cb,  # type: ignore[arg-type]
                **self.extra_options,
            )

    async def _serve_consume_queue(
        self,
        *,
        task_status: "TaskStatus[None]" = anyio.TASK_STATUS_IGNORED,
    ) -> None:
        """Endless task consuming messages from in-memory queue.

        Suitable to batch messages by amount, timestamps, etc and call `consume` for this batches.
        """
        async with anyio.create_task_group() as tg:
            task_status.started()

            async for msg in self.receive_stream:
                tg.start_soon(self._consume_msg, msg)

    async def _consume_pull(
        self,
        cb: Callable[["Msg"], Awaitable[SendableMessage]],
        *,
        task_status: "TaskStatus[None]" = anyio.TASK_STATUS_IGNORED,
    ) -> None:
        """Endless task consuming messages using NATS Pull subscriber."""
        assert self.pull_sub  # nosec B101

        sub = cast("JetStreamContext.PullSubscription", self.subscription)

        task_status.started()

        while self.running:  # pragma: no branch
            with suppress(TimeoutError):
                messages = await sub.fetch(
                    batch=self.pull_sub.batch_size,
                    timeout=self.pull_sub.timeout,
                )

                if messages:
                    async with anyio.create_task_group() as tg:
                        for msg in messages:
                            tg.start_soon(cb, msg)


class BatchHandler(BaseNatsHandler[List["Msg"]]):
    """Batch-message consumer class."""
    pull_sub: "PullSub"
    stream: "JStream"

    @override
    def add_call(  # type: ignore[override]
        self,
        *,
        filter: "Filter[StreamMessage[List[Msg]]]",
        parser: Optional["CustomParser[List[Msg]]"],
        decoder: Optional["CustomDecoder[StreamMessage[List[Msg]]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[List[Msg]]":
        return super().add_call(
            parser_=resolve_custom_func(parser, JsParser.parse_batch),
            decoder_=resolve_custom_func(decoder, JsParser.decode_batch),
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    @override
    async def create_subscription(  # type: ignore[override]
        self,
        connection: Annotated[
            "JetStreamContext",
            Doc("JS Context object using to create subscription"),
        ],
    ) -> None:
        """Create NATS subscription and start consume task."""
        self.subscription = await connection.pull_subscribe(
            subject=self.subject,
            **self.extra_options,
        )
        self.tasks.append(asyncio.create_task(self._consume_pull()))

    async def _consume_pull(
        self,
        *,
        task_status: "TaskStatus[None]" = anyio.TASK_STATUS_IGNORED,
    ) -> None:
        """Endless task consuming messages using NATS Pull subscriber."""
        sub = cast("JetStreamContext.PullSubscription", self.subscription)

        task_status.started()

        while self.running:  # pragma: no branch
            with suppress(TimeoutError):
                messages = await sub.fetch(
                    batch=self.pull_sub.batch_size,
                    timeout=self.pull_sub.timeout,
                )

                if messages:
                    await self.consume(messages)
