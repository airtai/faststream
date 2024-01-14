import logging
import warnings
from contextlib import AsyncExitStack
from functools import partial
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Type,
    Union,
)

import nats
from fast_depends.dependencies import Depends
from nats.aio.client import Callback, Client, ErrorCallback
from nats.aio.msg import Msg
from nats.aio.subscription import (
    DEFAULT_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_SUB_PENDING_MSGS_LIMIT,
)
from nats.js import api
from nats.js.client import (
    DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
    JetStreamContext,
)
from typing_extensions import TypeAlias, override

from faststream.broker.core.broker import BrokerUsecase, default_filter
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    SubscriberMiddleware,
)
from faststream.broker.utils import get_watcher_context
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.nats.asyncapi import Handler, Publisher
from faststream.nats.helpers import stream_builder
from faststream.nats.js_stream import JStream
from faststream.nats.message import NatsMessage
from faststream.nats.producer import NatsFastProducer, NatsJSFastProducer
from faststream.nats.pull_sub import PullSub
from faststream.nats.security import parse_security
from faststream.nats.shared.logging import NatsLoggingMixin
from faststream.security import BaseSecurity
from faststream.types import AnyDict, DecodedMessage, SendableMessage
from faststream.utils.context.repository import context

Subject: TypeAlias = str

if TYPE_CHECKING:
    from faststream.broker.core.handler import WrapperProtocol


class NatsBroker(
    NatsLoggingMixin,
    BrokerUsecase[Msg, Client],
):
    """A class to represent a NATS broker."""

    url: List[str]
    stream: Optional[JetStreamContext]

    handlers: Dict[Subject, Handler]
    _publishers: Dict[Subject, Publisher]
    _producer: Optional[NatsFastProducer]
    _js_producer: Optional[NatsJSFastProducer]

    def __init__(
        self,
        servers: Union[str, Sequence[str]] = ("nats://localhost:4222",),
        *,
        security: Optional[BaseSecurity] = None,
        protocol: str = "nats",
        protocol_version: Optional[str] = "custom",
        **kwargs: Any,
    ) -> None:
        """Initialize the NatsBroker object.

        Args:
            servers (Union[str, Sequence[str]]): The NATS server(s) to connect to.
            security (Optional[BaseSecurity]): The security options.
            protocol (str): The protocol to use.
            protocol_version (Optional[str]): The protocol version to use.
            **kwargs (Any): Additional keyword arguments.
        """
        kwargs.update(parse_security(security))

        if kwargs.get("tls"):  # pragma: no cover
            warnings.warn(
                (
                    "\nNATS `tls` option was deprecated and will be removed in 0.4.0"
                    "\nPlease, use `security` with `BaseSecurity` or `SASLPlaintext` instead"
                ),
                DeprecationWarning,
                stacklevel=2,
            )

        super().__init__(
            url=([servers] if isinstance(servers, str) else list(servers)),
            protocol=protocol,
            protocol_version=protocol_version,
            security=security,
            **kwargs,
        )

        self.__is_connected = False
        self._producer = None

        # JS options
        self.stream = None
        self._js_producer = None

    async def connect(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Client:
        connection = await super().connect(*args, **kwargs)
        for p in self._publishers.values():
            self.__set_publisher_producer(p)
        return connection

    async def _connect(
        self,
        error_cb: Optional[ErrorCallback] = None,
        reconnected_cb: Optional[Callback] = None,
        **kwargs: Any,
    ) -> Client:
        self.__is_connected = True

        connect = await nats.connect(
            error_cb=self._log_connection_broken(error_cb),
            reconnected_cb=self._log_reconnected(reconnected_cb),
            **kwargs,
        )

        self._producer = NatsFastProducer(
            connect,
            decoder=self._global_decoder,
            parser=self._global_parser,
        )

        stream = self.stream = connect.jetstream()

        self._js_producer = NatsJSFastProducer(
            stream,
            decoder=self._global_decoder,
            parser=self._global_parser,
        )

        return connect

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        self._producer = None
        self._js_producer = None
        self.stream = None

        if self._connection is not None:
            await self._connection.drain()

        await super()._close(exc_type, exc_val, exec_tb)
        self.__is_connected = False

    async def start(self) -> None:
        context.set_global(
            "default_log_context",
            self._get_log_context(None, ""),
        )

        await super().start()
        assert self._connection  # nosec B101
        assert self.stream, "Broker should be started already"  # nosec B101

        for handler in self.handlers.values():
            stream = handler.stream

            if (is_js := stream is not None) and stream.declare:
                try:  # pragma: no branch
                    await self.stream.add_stream(
                        config=stream.config,
                        subjects=stream.subjects,
                    )

                except nats.js.errors.BadRequestError as e:
                    old_config = (await self.stream.stream_info(stream.name)).config

                    c = self._get_log_context(None, "")
                    if (
                        e.description
                        == "stream name already in use with a different configuration"
                    ):
                        self._log(str(e), logging.WARNING, c)
                        await self.stream.update_stream(
                            config=stream.config,
                            subjects=tuple(
                                set(old_config.subjects or ()).union(stream.subjects)
                            ),
                        )

                    else:  # pragma: no cover
                        self._log(str(e), logging.ERROR, c, exc_info=e)

                finally:
                    # prevent from double declaration
                    stream.declare = False

            c = self._get_log_context(
                None,
                subject=handler.subject,
                queue=handler.queue,
                stream=stream.name if stream else "",
            )
            self._log(f"`{handler.call_name}` waiting for messages", extra=c)
            await handler.start(self.stream if is_js else self._connection)

    def _log_connection_broken(
        self,
        error_cb: Optional[ErrorCallback] = None,
    ) -> ErrorCallback:
        c = self._get_log_context(None, "")

        async def wrapper(err: Exception) -> None:
            if error_cb is not None:
                await error_cb(err)

            if self.__is_connected is True:
                self._log(str(err), logging.WARNING, c, exc_info=err)
                self.__is_connected = False

        return wrapper

    def _log_reconnected(
        self,
        cb: Optional[Callback] = None,
    ) -> Callback:
        c = self._get_log_context(None, "")

        async def wrapper() -> None:
            if cb is not None:
                await cb()

            if self.__is_connected is False:
                self._log("Connection established", logging.INFO, c)
                self.__is_connected = True

        return wrapper

    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        queue: str = "",
        pending_msgs_limit: Optional[int] = None,
        pending_bytes_limit: Optional[int] = None,
        # Core arguments
        max_msgs: int = 0,
        # JS arguments
        durable: Optional[str] = None,
        config: Optional[api.ConsumerConfig] = None,
        ordered_consumer: bool = False,
        idle_heartbeat: Optional[float] = None,
        flow_control: bool = False,
        deliver_policy: Optional[api.DeliverPolicy] = None,
        headers_only: Optional[bool] = None,
        # pull arguments
        pull_sub: Optional[PullSub] = None,
        inbox_prefix: bytes = api.INBOX_PREFIX,
        # custom
        ack_first: bool = False,
        stream: Union[str, JStream, None] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[Msg, NatsMessage]] = None,
        decoder: Optional[CustomDecoder[NatsMessage]] = None,
        middlewares: Iterable[SubscriberMiddleware] = (),
        filter: Filter[NatsMessage] = default_filter,
        max_workers: int = 1,
        retry: bool = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        **wrapper_kwargs: Any,
    ) -> "WrapperProtocol[Msg]":
        stream = stream_builder.stream(stream)

        if pull_sub is not None and stream is None:
            raise ValueError("Pull subscriber can be used only with a stream")

        self._setup_log_context(
            queue=queue,
            subject=subject,
            stream=stream.name if stream else None,
        )
        super().subscriber()

        extra_options: AnyDict = {
            "pending_msgs_limit": pending_msgs_limit
            or (
                DEFAULT_JS_SUB_PENDING_MSGS_LIMIT
                if stream
                else DEFAULT_SUB_PENDING_MSGS_LIMIT
            ),
            "pending_bytes_limit": pending_bytes_limit
            or (
                DEFAULT_JS_SUB_PENDING_BYTES_LIMIT
                if stream
                else DEFAULT_SUB_PENDING_BYTES_LIMIT
            ),
        }

        if stream:
            extra_options.update(
                {
                    "durable": durable,
                    "stream": stream.name,
                    "config": config,
                }
            )

            if pull_sub is not None:
                extra_options.update({"inbox_prefix": inbox_prefix})

            else:
                extra_options.update(
                    {
                        "ordered_consumer": ordered_consumer,
                        "idle_heartbeat": idle_heartbeat,
                        "flow_control": flow_control,
                        "deliver_policy": deliver_policy,
                        "headers_only": headers_only,
                        "manual_ack": not ack_first,
                    }
                )

        else:
            extra_options.update(
                {
                    "max_msgs": max_msgs,
                }
            )

        key = Handler.get_routing_hash(subject)
        handler = self.handlers[key] = self.handlers.get(
            key,
            Handler(
                subject=subject,
                queue=queue,
                stream=stream,
                pull_sub=pull_sub,
                extra_options=extra_options,
                max_workers=max_workers,
                producer=self,
                # base options
                title=title,
                description=description,
                include_in_schema=include_in_schema,
                graceful_timeout=self.graceful_timeout,
                middlewares=self.middlewares,
                log_context_builder=partial(
                    self._get_log_context,
                    stream=stream.name if stream else "",
                    subject=subject,
                    queue=queue,
                ),
                watcher=get_watcher_context(self.logger, no_ack, retry),
            ),
        )

        if stream:
            stream.subjects.append(handler.subject)

        return handler.add_call(
            filter=filter,
            parser=parser or self._global_parser,
            decoder=decoder or self._global_decoder,
            dependencies=(*self.dependencies, *dependencies),
            middlewares=middlewares,
            # wrapper kwargs
            is_validate=self._is_validate,
            apply_types=self._is_apply_types,
            **wrapper_kwargs,
        )

    @override
    def publisher(  # type: ignore[override]
        self,
        subject: str,
        headers: Optional[Dict[str, str]] = None,
        # Core
        reply_to: str = "",
        # JS
        stream: Union[str, JStream, None] = None,
        timeout: Optional[float] = None,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> Publisher:
        if (stream := stream_builder.stream(stream)) is not None:
            stream.subjects.append(subject)

        publisher = self._publishers.get(
            subject,
            Publisher(
                subject=subject,
                headers=headers,
                # Core
                reply_to=reply_to,
                # JS
                timeout=timeout,
                stream=stream,
                # AsyncAPI
                title=title,
                _description=description,
                _schema=schema,
                include_in_schema=include_in_schema,
            ),
        )
        super().publisher(subject, publisher)
        self.__set_publisher_producer(publisher)
        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
        *args: Any,
        stream: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[DecodedMessage]:
        if stream is None:
            assert self._producer, NOT_CONNECTED_YET  # nosec B101
            publisher = self._producer
        else:
            assert self._js_producer, NOT_CONNECTED_YET  # nosec B101
            publisher = self._js_producer
            kwargs["stream"] = stream

        async with AsyncExitStack() as stack:
            for m in self.middlewares:
                message = await stack.enter_async_context(
                    m(None).publish_scope(message)
                )

            return await publisher.publish(message, *args, **kwargs)

    def __set_publisher_producer(self, publisher: Publisher) -> None:
        if publisher.stream is not None:
            if self._js_producer is not None:
                publisher._producer = self._js_producer
        elif self._producer is not None:
            publisher._producer = self._producer
