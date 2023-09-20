import logging
from functools import partial, wraps
from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Type, Union

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

from faststream._compat import override
from faststream.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.push_back_watcher import BaseWatcher, WatcherContext
from faststream.broker.types import (
    AsyncPublisherProtocol,
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import FakePublisher, HandlerCallWrapper
from faststream.nats.asyncapi import Handler, Publisher
from faststream.nats.js_stream import JsStream
from faststream.nats.message import NatsMessage
from faststream.nats.producer import NatsFastProducer, NatsJSFastProducer
from faststream.nats.shared.logging import NatsLoggingMixin
from faststream.types import DecodedMessage
from faststream.utils.context.main import context
from faststream.utils.functions import to_async

Subject = str


class NatsBroker(
    NatsLoggingMixin,
    BrokerAsyncUsecase[Msg, Client],
):
    _stream: Optional[JetStreamContext]

    handlers: Dict[Subject, Handler]
    _publishers: Dict[Subject, Publisher]
    _producer: Optional[NatsFastProducer]
    _js_producer: Optional[NatsJSFastProducer]

    def __init__(
        self,
        servers: Union[str, Sequence[str]] = ("nats://localhost:4222",),  # noqa: B006
        *,
        protocol: str = "nats",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            url=servers,  # AsyncAPI information
            protocol=protocol,
            servers=list(servers),  # nats-py connect argument
            **kwargs,
        )

        self.__is_connected = False
        self._producer = None

        # JS options
        self._stream = None
        self._js_producer = None

    async def connect(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Client:
        connection = await super().connect(*args, **kwargs)
        for p in self._publishers.values():
            if p.stream is not None:
                p._producer = self._js_producer
            else:
                p._producer = self._producer
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

        stream = self._stream = connect.jetstream()

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
        self._stream = None

        if self._connection is not None:
            await self._connection.drain()

        await super()._close(exc_type, exc_val, exec_tb)
        self.__is_connected = False

    async def start(self) -> None:
        context.set_local(
            "log_context",
            self._get_log_context(None, ""),
        )

        await super().start()
        assert self._connection

        for handler in self.handlers.values():
            stream = handler.stream

            if (is_js := stream is not None) and stream.declare:
                try:  # pragma: no branch
                    await self._stream.add_stream(
                        config=stream.config,
                        subjects=stream.subjects,
                    )

                except nats.js.errors.BadRequestError as e:
                    old_config = (await self._stream.stream_info(stream.name)).config

                    c = self._get_log_context(None, "")
                    if (
                        e.description
                        == "stream name already in use with a different configuration"
                    ):
                        self._log(e, logging.WARNING, c)
                        await self._stream.update_stream(
                            config=stream.config,
                            subjects=tuple(
                                set(old_config.subjects).union(stream.subjects)
                            ),
                        )

                    else:  # pragma: no cover
                        self._log(e, logging.ERROR, c, exc_info=e)

                finally:
                    # prevent from double declaration
                    stream.declare = False

            c = self._get_log_context(
                None,
                subject=handler.subject,
                queue=handler.queue,
                stream=stream.name if stream else "",
            )
            self._log(f"`{handler.name}` waiting for messages", extra=c)
            await handler.start(self._stream if is_js else self._connection)

    def _process_message(
        self,
        func: Callable[[NatsMessage], Awaitable[T_HandlerReturn]],
        watcher: BaseWatcher,
    ) -> Callable[[NatsMessage], Awaitable[WrappedReturn[T_HandlerReturn]]]:
        @wraps(func)
        async def process_wrapper(
            message: NatsMessage,
        ) -> WrappedReturn[T_HandlerReturn]:
            async with WatcherContext(watcher, message):
                r = await self._execute_handler(func, message)

                pub_response: Optional[AsyncPublisherProtocol]
                if message.reply_to:
                    pub_response = FakePublisher(
                        partial(self.publish, subject=message.reply_to)
                    )
                else:
                    pub_response = None

                return r, pub_response

            raise AssertionError("unreachable")

        return process_wrapper

    def _log_connection_broken(
        self,
        error_cb: Optional[ErrorCallback] = None,
    ) -> ErrorCallback:
        c = self._get_log_context(None, "")

        async def wrapper(err: Exception) -> None:
            if error_cb is not None:
                await error_cb(err)

            if self.__is_connected is True:
                self._log(err, logging.WARNING, c, exc_info=err)
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
        # custom
        ack_first: bool = False,
        stream: Union[str, JsStream, None] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[Msg]] = None,
        decoder: Optional[CustomDecoder[Msg]] = None,
        middlewares: Optional[Sequence[Callable[[Msg], BaseMiddleware]]] = None,
        filter: Filter[NatsMessage] = default_filter,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **original_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
    ]:
        stream = JsStream.validate(stream)
        is_js = stream is not None

        self._setup_log_context(
            queue=queue,
            subject=subject,
            stream=stream.name if is_js else None,
        )
        super().subscriber()

        extra_options = {
            "pending_msgs_limit": pending_msgs_limit
            or (
                DEFAULT_JS_SUB_PENDING_MSGS_LIMIT
                if is_js
                else DEFAULT_SUB_PENDING_MSGS_LIMIT
            ),
            "pending_bytes_limit": pending_bytes_limit
            or (
                DEFAULT_JS_SUB_PENDING_BYTES_LIMIT
                if is_js
                else DEFAULT_SUB_PENDING_BYTES_LIMIT
            ),
        }

        if is_js:
            stream.subjects.append(subject)
            extra_options.update(
                {
                    "durable": durable,
                    "config": config,
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

        handler = self.handlers[subject] = self.handlers.get(
            subject,
            Handler(
                subject=subject,
                queue=queue,
                stream=stream,
                extra_options=extra_options,
                title=title,
                description=description,
            ),
        )

        def consumer_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn,]:
            handler_call, dependant = self._wrap_handler(
                func,
                extra_dependencies=dependencies,
                **original_kwargs,
                stream=stream.name if stream else "",
                subject=subject,
                queue=queue,
            )

            handler.add_call(
                handler=handler_call,
                filter=to_async(filter),
                middlewares=middlewares,
                parser=parser or self._global_parser,
                decoder=decoder or self._global_decoder,
                dependant=dependant,
            )

            return handler_call

        return consumer_wrapper

    @override
    def publisher(  # type: ignore[override]
        self,
        subject: str,
        headers: Optional[Dict[str, str]] = None,
        # Core
        reply_to: str = "",
        # JS
        stream: Union[str, JsStream, None] = None,
        timeout: Optional[float] = None,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Publisher:
        publisher = self._publishers.get(
            subject,
            Publisher(
                subject=subject,
                headers=headers,
                # Core
                reply_to=reply_to,
                # JS
                timeout=timeout,
                stream=JsStream.validate(stream),
                # AsyncAPI
                title=title,
                _description=description,
            ),
        )
        super().publisher(subject, publisher)
        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[DecodedMessage]:
        assert self._producer, "NatsBroker is not started yet"  # nosec B101
        return await self._producer.publish(*args, **kwargs)
