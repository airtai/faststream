from abc import abstractmethod
from collections.abc import Awaitable, Iterable
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Generic,
    Optional,
    cast,
)

import anyio
from nats.errors import ConnectionClosedError, TimeoutError
from nats.js.api import ConsumerConfig, ObjectInfo
from typing_extensions import Doc, override

from faststream._internal.subscriber.mixins import ConcurrentMixin, TasksMixin
from faststream._internal.subscriber.usecase import SubscriberUsecase
from faststream._internal.subscriber.utils import process_msg
from faststream._internal.types import MsgType
from faststream.middlewares import AckPolicy
from faststream.nats.helpers import KVBucketDeclarer, OSBucketDeclarer
from faststream.nats.message import NatsMessage
from faststream.nats.parser import (
    BatchParser,
    JsParser,
    KvParser,
    NatsParser,
    ObjParser,
)
from faststream.nats.publisher.fake import NatsFakePublisher
from faststream.nats.schemas.js_stream import compile_nats_wildcard
from faststream.nats.subscriber.adapters import (
    UnsubscribeAdapter,
    Unsubscriptable,
)

from .state import ConnectedSubscriberState, EmptySubscriberState, SubscriberState

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant
    from nats.aio.msg import Msg
    from nats.aio.subscription import Subscription
    from nats.js import JetStreamContext
    from nats.js.kv import KeyValue
    from nats.js.object_store import ObjectStore

    from faststream._internal.basic_types import (
        AnyDict,
        SendableMessage,
    )
    from faststream._internal.publisher.proto import BasePublisherProto, ProducerProto
    from faststream._internal.state import BrokerState as BasicState
    from faststream._internal.types import (
        AsyncCallable,
        BrokerMiddleware,
        CustomCallable,
    )
    from faststream.message import StreamMessage
    from faststream.nats.broker.state import BrokerState
    from faststream.nats.helpers import KVBucketDeclarer, OSBucketDeclarer
    from faststream.nats.message import NatsKvMessage, NatsObjMessage
    from faststream.nats.schemas import JStream, KvWatch, ObjWatch, PullSub


class LogicSubscriber(SubscriberUsecase[MsgType], Generic[MsgType]):
    """A class to represent a NATS handler."""

    subscription: Optional[Unsubscriptable]
    _fetch_sub: Optional[Unsubscriptable]
    producer: Optional["ProducerProto"]

    def __init__(
        self,
        *,
        subject: str,
        config: "ConsumerConfig",
        extra_options: Optional["AnyDict"],
        # Subscriber args
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[MsgType]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        self.subject = subject
        self.config = config

        self.extra_options = extra_options or {}

        super().__init__(
            default_parser=default_parser,
            default_decoder=default_decoder,
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self._fetch_sub = None
        self.subscription = None
        self.producer = None

        self._connection_state: SubscriberState = EmptySubscriberState()

    @override
    def _setup(  # type: ignore[override]
        self,
        *,
        connection_state: "BrokerState",
        os_declarer: "OSBucketDeclarer",
        kv_declarer: "KVBucketDeclarer",
        # basic args
        extra_context: "AnyDict",
        # broker options
        broker_parser: Optional["CustomCallable"],
        broker_decoder: Optional["CustomCallable"],
        # dependant args
        state: "BasicState",
    ) -> None:
        self._connection_state = ConnectedSubscriberState(
            parent_state=connection_state,
            os_declarer=os_declarer,
            kv_declarer=kv_declarer,
        )

        super()._setup(
            extra_context=extra_context,
            broker_parser=broker_parser,
            broker_decoder=broker_decoder,
            state=state,
        )

    @property
    def clear_subject(self) -> str:
        """Compile `test.{name}` to `test.*` subject."""
        _, path = compile_nats_wildcard(self.subject)
        return path

    async def start(self) -> None:
        """Create NATS subscription and start consume tasks."""
        await super().start()

        if self.calls:
            await self._create_subscription()

    async def close(self) -> None:
        """Clean up handler subscription, cancel consume task in graceful mode."""
        await super().close()

        if self.subscription is not None:
            await self.subscription.unsubscribe()
            self.subscription = None

        if self._fetch_sub is not None:
            await self._fetch_sub.unsubscribe()
            self.subscription = None

    @abstractmethod
    async def _create_subscription(self) -> None:
        """Create NATS subscription object to consume messages."""
        raise NotImplementedError

    @staticmethod
    def build_log_context(
        message: Annotated[
            Optional["StreamMessage[MsgType]"],
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
            str,
            Doc("Stream object we are listening"),
        ] = "",
    ) -> dict[str, str]:
        """Static method to build log context out of `self.consume` scope."""
        return {
            "subject": subject,
            "queue": queue,
            "stream": stream,
            "message_id": getattr(message, "message_id", ""),
        }

    def add_prefix(self, prefix: str) -> None:
        """Include Subscriber in router."""
        if self.subject:
            self.subject = f"{prefix}{self.subject}"
        else:
            self.config.filter_subjects = [
                f"{prefix}{subject}" for subject in (self.config.filter_subjects or ())
            ]

    @property
    def _resolved_subject_string(self) -> str:
        return self.subject or ", ".join(self.config.filter_subjects or ())


class _DefaultSubscriber(LogicSubscriber[MsgType]):
    def __init__(
        self,
        *,
        subject: str,
        config: "ConsumerConfig",
        # default args
        extra_options: Optional["AnyDict"],
        # Subscriber args
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[MsgType]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            subject=subject,
            config=config,
            extra_options=extra_options,
            # subscriber args
            default_parser=default_parser,
            default_decoder=default_decoder,
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    def _make_response_publisher(
        self,
        message: "StreamMessage[Any]",
    ) -> Iterable["BasePublisherProto"]:
        """Create Publisher objects to use it as one of `publishers` in `self.consume` scope."""
        return (
            NatsFakePublisher(
                producer=self._state.producer,
                subject=message.reply_to,
            ),
        )

    def get_log_context(
        self,
        message: Annotated[
            Optional["StreamMessage[MsgType]"],
            Doc("Message which we are building context for"),
        ],
    ) -> dict[str, str]:
        """Log context factory using in `self.consume` scope."""
        return self.build_log_context(
            message=message,
            subject=self.subject,
        )


class CoreSubscriber(_DefaultSubscriber["Msg"]):
    subscription: Optional["Subscription"]
    _fetch_sub: Optional["Subscription"]

    def __init__(
        self,
        *,
        # default args
        subject: str,
        config: "ConsumerConfig",
        queue: str,
        extra_options: Optional["AnyDict"],
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser_ = NatsParser(pattern=subject, ack_policy=ack_policy)

        self.queue = queue

        super().__init__(
            subject=subject,
            config=config,
            extra_options=extra_options,
            # subscriber args
            default_parser=parser_.parse_message,
            default_decoder=parser_.decode_message,
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def get_one(
        self,
        *,
        timeout: float = 5.0,
    ) -> "Optional[NatsMessage]":
        assert (  # nosec B101
            not self.calls
        ), "You can't use `get_one` method if subscriber has registered handlers."

        if self._fetch_sub is None:
            fetch_sub = self._fetch_sub = await self._connection_state.client.subscribe(
                subject=self.clear_subject,
                queue=self.queue,
                **self.extra_options,
            )
        else:
            fetch_sub = self._fetch_sub

        try:
            raw_message = await fetch_sub.next_msg(timeout=timeout)
        except TimeoutError:
            return None

        msg: NatsMessage = await process_msg(  # type: ignore[assignment]
            msg=raw_message,
            middlewares=(
                m(raw_message, context=self._state.di_state.context)
                for m in self._broker_middlewares
            ),
            parser=self._parser,
            decoder=self._decoder,
        )
        return msg

    @override
    async def _create_subscription(self) -> None:
        """Create NATS subscription and start consume task."""
        if self.subscription:
            return

        self.subscription = await self._connection_state.client.subscribe(
            subject=self.clear_subject,
            queue=self.queue,
            cb=self.consume,
            **self.extra_options,
        )

    def get_log_context(
        self,
        message: Annotated[
            Optional["StreamMessage[Msg]"],
            Doc("Message which we are building context for"),
        ],
    ) -> dict[str, str]:
        """Log context factory using in `self.consume` scope."""
        return self.build_log_context(
            message=message,
            subject=self.subject,
            queue=self.queue,
        )


class ConcurrentCoreSubscriber(
    ConcurrentMixin,
    CoreSubscriber,
):
    def __init__(
        self,
        *,
        max_workers: int,
        # default args
        subject: str,
        config: "ConsumerConfig",
        queue: str,
        extra_options: Optional["AnyDict"],
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            max_workers=max_workers,
            # basic args
            subject=subject,
            config=config,
            queue=queue,
            extra_options=extra_options,
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def _create_subscription(self) -> None:
        """Create NATS subscription and start consume task."""
        if self.subscription:
            return

        self.start_consume_task()

        self.subscription = await self._connection_state.client.subscribe(
            subject=self.clear_subject,
            queue=self.queue,
            cb=self._put_msg,
            **self.extra_options,
        )


class _StreamSubscriber(_DefaultSubscriber["Msg"]):
    _fetch_sub: Optional["JetStreamContext.PullSubscription"]

    def __init__(
        self,
        *,
        stream: "JStream",
        # default args
        subject: str,
        config: "ConsumerConfig",
        queue: str,
        extra_options: Optional["AnyDict"],
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser_ = JsParser(pattern=subject)

        self.queue = queue
        self.stream = stream

        super().__init__(
            subject=subject,
            config=config,
            extra_options=extra_options,
            # subscriber args
            default_parser=parser_.parse_message,
            default_decoder=parser_.decode_message,
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    def get_log_context(
        self,
        message: Annotated[
            Optional["StreamMessage[Msg]"],
            Doc("Message which we are building context for"),
        ],
    ) -> dict[str, str]:
        """Log context factory using in `self.consume` scope."""
        return self.build_log_context(
            message=message,
            subject=self._resolved_subject_string,
            queue=self.queue,
            stream=self.stream.name,
        )

    @override
    async def get_one(
        self,
        *,
        timeout: float = 5,
    ) -> Optional["NatsMessage"]:
        assert (  # nosec B101
            not self.calls
        ), "You can't use `get_one` method if subscriber has registered handlers."

        if not self._fetch_sub:
            extra_options = {
                "pending_bytes_limit": self.extra_options["pending_bytes_limit"],
                "pending_msgs_limit": self.extra_options["pending_msgs_limit"],
                "durable": self.extra_options["durable"],
                "stream": self.extra_options["stream"],
            }
            if inbox_prefix := self.extra_options.get("inbox_prefix"):
                extra_options["inbox_prefix"] = inbox_prefix

            self._fetch_sub = await self._connection_state.js.pull_subscribe(
                subject=self.clear_subject,
                config=self.config,
                **extra_options,
            )

        try:
            raw_message = (
                await self._fetch_sub.fetch(
                    batch=1,
                    timeout=timeout,
                )
            )[0]
        except (TimeoutError, ConnectionClosedError):
            return None

        msg: NatsMessage = await process_msg(  # type: ignore[assignment]
            msg=raw_message,
            middlewares=(
                m(raw_message, context=self._state.di_state.context)
                for m in self._broker_middlewares
            ),
            parser=self._parser,
            decoder=self._decoder,
        )
        return msg


class PushStreamSubscription(_StreamSubscriber):
    subscription: Optional["JetStreamContext.PushSubscription"]

    @override
    async def _create_subscription(self) -> None:
        """Create NATS subscription and start consume task."""
        if self.subscription:
            return

        self.subscription = await self._connection_state.js.subscribe(
            subject=self.clear_subject,
            queue=self.queue,
            cb=self.consume,
            config=self.config,
            **self.extra_options,
        )


class ConcurrentPushStreamSubscriber(
    ConcurrentMixin,
    _StreamSubscriber,
):
    subscription: Optional["JetStreamContext.PushSubscription"]

    def __init__(
        self,
        *,
        max_workers: int,
        stream: "JStream",
        # default args
        subject: str,
        config: "ConsumerConfig",
        queue: str,
        extra_options: Optional["AnyDict"],
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            max_workers=max_workers,
            # basic args
            stream=stream,
            subject=subject,
            config=config,
            queue=queue,
            extra_options=extra_options,
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def _create_subscription(self) -> None:
        """Create NATS subscription and start consume task."""
        if self.subscription:
            return

        self.start_consume_task()

        self.subscription = await self._connection_state.js.subscribe(
            subject=self.clear_subject,
            queue=self.queue,
            cb=self._put_msg,
            config=self.config,
            **self.extra_options,
        )


class PullStreamSubscriber(
    TasksMixin,
    _StreamSubscriber,
):
    subscription: Optional["JetStreamContext.PullSubscription"]

    def __init__(
        self,
        *,
        pull_sub: "PullSub",
        stream: "JStream",
        # default args
        subject: str,
        config: "ConsumerConfig",
        extra_options: Optional["AnyDict"],
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        self.pull_sub = pull_sub

        super().__init__(
            # basic args
            stream=stream,
            subject=subject,
            config=config,
            extra_options=extra_options,
            queue="",
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def _create_subscription(self) -> None:
        """Create NATS subscription and start consume task."""
        if self.subscription:
            return

        self.subscription = await self._connection_state.js.pull_subscribe(
            subject=self.clear_subject,
            config=self.config,
            **self.extra_options,
        )
        self.add_task(self._consume_pull(cb=self.consume))

    async def _consume_pull(
        self,
        cb: Callable[["Msg"], Awaitable["SendableMessage"]],
    ) -> None:
        """Endless task consuming messages using NATS Pull subscriber."""
        assert self.subscription  # nosec B101

        while self.running:  # pragma: no branch
            messages = []
            with suppress(TimeoutError, ConnectionClosedError):
                messages = await self.subscription.fetch(
                    batch=self.pull_sub.batch_size,
                    timeout=self.pull_sub.timeout,
                )

            if messages:
                async with anyio.create_task_group() as tg:
                    for msg in messages:
                        tg.start_soon(cb, msg)


class ConcurrentPullStreamSubscriber(
    ConcurrentMixin,
    PullStreamSubscriber,
):
    def __init__(
        self,
        *,
        max_workers: int,
        # default args
        pull_sub: "PullSub",
        stream: "JStream",
        subject: str,
        config: "ConsumerConfig",
        extra_options: Optional["AnyDict"],
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            max_workers=max_workers,
            # basic args
            pull_sub=pull_sub,
            stream=stream,
            subject=subject,
            config=config,
            extra_options=extra_options,
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def _create_subscription(self) -> None:
        """Create NATS subscription and start consume task."""
        if self.subscription:
            return

        self.start_consume_task()

        self.subscription = await self._connection_state.js.pull_subscribe(
            subject=self.clear_subject,
            config=self.config,
            **self.extra_options,
        )
        self.add_task(self._consume_pull(cb=self._put_msg))


class BatchPullStreamSubscriber(
    TasksMixin,
    _DefaultSubscriber[list["Msg"]],
):
    """Batch-message consumer class."""

    subscription: Optional["JetStreamContext.PullSubscription"]
    _fetch_sub: Optional["JetStreamContext.PullSubscription"]

    def __init__(
        self,
        *,
        # default args
        subject: str,
        config: "ConsumerConfig",
        stream: "JStream",
        pull_sub: "PullSub",
        extra_options: Optional["AnyDict"],
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[list[Msg]]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = BatchParser(pattern=subject)

        self.stream = stream
        self.pull_sub = pull_sub

        super().__init__(
            subject=subject,
            config=config,
            extra_options=extra_options,
            # subscriber args
            default_parser=parser.parse_batch,
            default_decoder=parser.decode_batch,
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def get_one(
        self,
        *,
        timeout: float = 5,
    ) -> Optional["NatsMessage"]:
        assert (  # nosec B101
            not self.calls
        ), "You can't use `get_one` method if subscriber has registered handlers."

        if not self._fetch_sub:
            fetch_sub = (
                self._fetch_sub
            ) = await self._connection_state.js.pull_subscribe(
                subject=self.clear_subject,
                config=self.config,
                **self.extra_options,
            )
        else:
            fetch_sub = self._fetch_sub

        try:
            raw_message = await fetch_sub.fetch(
                batch=1,
                timeout=timeout,
            )
        except TimeoutError:
            return None

        return cast(
            NatsMessage,
            await process_msg(
                msg=raw_message,
                middlewares=(
                    m(raw_message, context=self._state.di_state.context)
                    for m in self._broker_middlewares
                ),
                parser=self._parser,
                decoder=self._decoder,
            ),
        )

    @override
    async def _create_subscription(self) -> None:
        """Create NATS subscription and start consume task."""
        if self.subscription:
            return

        self.subscription = await self._connection_state.js.pull_subscribe(
            subject=self.clear_subject,
            config=self.config,
            **self.extra_options,
        )
        self.add_task(self._consume_pull())

    async def _consume_pull(self) -> None:
        """Endless task consuming messages using NATS Pull subscriber."""
        assert self.subscription, "You should call `create_subscription` at first."  # nosec B101

        while self.running:  # pragma: no branch
            with suppress(TimeoutError, ConnectionClosedError):
                messages = await self.subscription.fetch(
                    batch=self.pull_sub.batch_size,
                    timeout=self.pull_sub.timeout,
                )

                if messages:
                    await self.consume(messages)


class KeyValueWatchSubscriber(
    TasksMixin,
    LogicSubscriber["KeyValue.Entry"],
):
    subscription: Optional["UnsubscribeAdapter[KeyValue.KeyWatcher]"]
    _fetch_sub: Optional[UnsubscribeAdapter["KeyValue.KeyWatcher"]]

    def __init__(
        self,
        *,
        subject: str,
        config: "ConsumerConfig",
        kv_watch: "KvWatch",
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[KeyValue.Entry]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = KvParser(pattern=subject)
        self.kv_watch = kv_watch

        super().__init__(
            subject=subject,
            config=config,
            extra_options=None,
            ack_policy=AckPolicy.DO_NOTHING,
            no_reply=True,
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def get_one(
        self,
        *,
        timeout: float = 5,
    ) -> Optional["NatsKvMessage"]:
        assert (  # nosec B101
            not self.calls
        ), "You can't use `get_one` method if subscriber has registered handlers."

        if not self._fetch_sub:
            bucket = await self._connection_state.kv_declarer.create_key_value(
                bucket=self.kv_watch.name,
                declare=self.kv_watch.declare,
            )

            fetch_sub = self._fetch_sub = UnsubscribeAdapter["KeyValue.KeyWatcher"](
                await bucket.watch(
                    keys=self.clear_subject,
                    headers_only=self.kv_watch.headers_only,
                    include_history=self.kv_watch.include_history,
                    ignore_deletes=self.kv_watch.ignore_deletes,
                    meta_only=self.kv_watch.meta_only,
                ),
            )
        else:
            fetch_sub = self._fetch_sub

        raw_message = None
        sleep_interval = timeout / 10
        with anyio.move_on_after(timeout):
            while (  # noqa: ASYNC110
                # type: ignore[no-untyped-call]
                raw_message := await fetch_sub.obj.updates(timeout)
            ) is None:
                await anyio.sleep(sleep_interval)

        msg: NatsKvMessage = await process_msg(
            msg=raw_message,
            middlewares=(
                m(raw_message, context=self._state.di_state.context)
                for m in self._broker_middlewares
            ),
            parser=self._parser,
            decoder=self._decoder,
        )
        return msg

    @override
    async def _create_subscription(self) -> None:
        if self.subscription:
            return

        bucket = await self._connection_state.kv_declarer.create_key_value(
            bucket=self.kv_watch.name,
            declare=self.kv_watch.declare,
        )

        self.subscription = UnsubscribeAdapter["KeyValue.KeyWatcher"](
            await bucket.watch(
                keys=self.clear_subject,
                headers_only=self.kv_watch.headers_only,
                include_history=self.kv_watch.include_history,
                ignore_deletes=self.kv_watch.ignore_deletes,
                meta_only=self.kv_watch.meta_only,
            ),
        )

        self.add_task(self.__consume_watch())

    async def __consume_watch(self) -> None:
        assert self.subscription, "You should call `create_subscription` at first."  # nosec B101

        key_watcher = self.subscription.obj

        while self.running:
            with suppress(ConnectionClosedError, TimeoutError):
                message = cast(
                    Optional["KeyValue.Entry"],
                    # type: ignore[no-untyped-call]
                    await key_watcher.updates(self.kv_watch.timeout),
                )

                if message:
                    await self.consume(message)

    def _make_response_publisher(
        self,
        message: Annotated[
            "StreamMessage[KeyValue.Entry]",
            Doc("Message requiring reply"),
        ],
    ) -> Iterable["BasePublisherProto"]:
        """Create Publisher objects to use it as one of `publishers` in `self.consume` scope."""
        return ()

    def get_log_context(
        self,
        message: Annotated[
            Optional["StreamMessage[KeyValue.Entry]"],
            Doc("Message which we are building context for"),
        ],
    ) -> dict[str, str]:
        """Log context factory using in `self.consume` scope."""
        return self.build_log_context(
            message=message,
            subject=self.subject,
            stream=self.kv_watch.name,
        )


OBJECT_STORAGE_CONTEXT_KEY = "__object_storage"


class ObjStoreWatchSubscriber(
    TasksMixin,
    LogicSubscriber[ObjectInfo],
):
    subscription: Optional["UnsubscribeAdapter[ObjectStore.ObjectWatcher]"]
    _fetch_sub: Optional[UnsubscribeAdapter["ObjectStore.ObjectWatcher"]]

    def __init__(
        self,
        *,
        subject: str,
        config: "ConsumerConfig",
        obj_watch: "ObjWatch",
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[list[Msg]]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = ObjParser(pattern="")

        self.obj_watch = obj_watch
        self.obj_watch_conn = None

        super().__init__(
            subject=subject,
            config=config,
            extra_options=None,
            ack_policy=AckPolicy.DO_NOTHING,
            no_reply=True,
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def get_one(
        self,
        *,
        timeout: float = 5,
    ) -> Optional["NatsObjMessage"]:
        assert (  # nosec B101
            not self.calls
        ), "You can't use `get_one` method if subscriber has registered handlers."

        if not self._fetch_sub:
            self.bucket = await self._connection_state.os_declarer.create_object_store(
                bucket=self.subject,
                declare=self.obj_watch.declare,
            )

            obj_watch = await self.bucket.watch(
                ignore_deletes=self.obj_watch.ignore_deletes,
                include_history=self.obj_watch.include_history,
                meta_only=self.obj_watch.meta_only,
            )
            fetch_sub = self._fetch_sub = UnsubscribeAdapter[
                "ObjectStore.ObjectWatcher"
            ](obj_watch)
        else:
            fetch_sub = self._fetch_sub

        raw_message = None
        sleep_interval = timeout / 10
        with anyio.move_on_after(timeout):
            while (  # noqa: ASYNC110
                # type: ignore[no-untyped-call]
                raw_message := await fetch_sub.obj.updates(timeout)
            ) is None:
                await anyio.sleep(sleep_interval)

        msg: NatsObjMessage = await process_msg(
            msg=raw_message,
            middlewares=(
                m(raw_message, context=self._state.di_state.context)
                for m in self._broker_middlewares
            ),
            parser=self._parser,
            decoder=self._decoder,
        )
        return msg

    @override
    async def _create_subscription(self) -> None:
        if self.subscription:
            return

        self.bucket = await self._connection_state.os_declarer.create_object_store(
            bucket=self.subject,
            declare=self.obj_watch.declare,
        )

        self.add_task(self.__consume_watch())

    async def __consume_watch(self) -> None:
        assert self.bucket, "You should call `create_subscription` at first."  # nosec B101

        # Should be created inside task to avoid nats-py lock
        obj_watch = await self.bucket.watch(
            ignore_deletes=self.obj_watch.ignore_deletes,
            include_history=self.obj_watch.include_history,
            meta_only=self.obj_watch.meta_only,
        )

        self.subscription = UnsubscribeAdapter["ObjectStore.ObjectWatcher"](obj_watch)

        while self.running:
            with suppress(TimeoutError):
                message = cast(
                    Optional["ObjectInfo"],
                    # type: ignore[no-untyped-call]
                    await obj_watch.updates(self.obj_watch.timeout),
                )

                if message:
                    with self._state.di_state.context.scope(
                        OBJECT_STORAGE_CONTEXT_KEY, self.bucket
                    ):
                        await self.consume(message)

    def _make_response_publisher(
        self,
        message: Annotated[
            "StreamMessage[ObjectInfo]",
            Doc("Message requiring reply"),
        ],
    ) -> Iterable["BasePublisherProto"]:
        """Create Publisher objects to use it as one of `publishers` in `self.consume` scope."""
        return ()

    def get_log_context(
        self,
        message: Annotated[
            Optional["StreamMessage[ObjectInfo]"],
            Doc("Message which we are building context for"),
        ],
    ) -> dict[str, str]:
        """Log context factory using in `self.consume` scope."""
        return self.build_log_context(
            message=message,
            subject=self.subject,
        )
