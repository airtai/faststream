import asyncio
from abc import abstractmethod
from contextlib import AsyncExitStack, suppress
from dataclasses import dataclass
from functools import partial, wraps
from inspect import unwrap
from logging import Logger
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import anyio
from fast_depends.core import CallModel, build_call_model
from fast_depends.dependencies import Depends
from typing_extensions import Self, override

from faststream._compat import IS_OPTIMIZED
from faststream.asyncapi.base import AsyncAPIOperation
from faststream.asyncapi.message import parse_handler_params
from faststream.asyncapi.utils import to_camelcase
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.push_back_watcher import WatcherContext
from faststream.broker.types import (
    AsyncDecoder,
    AsyncParser,
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.utils import get_watcher, set_message_context
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.exceptions import HandlerException, StopConsume
from faststream.types import AnyDict, SendableMessage
from faststream.utils import apply_types
from faststream.utils.context.repository import context
from faststream.utils.functions import fake_context, to_async

if TYPE_CHECKING:
    from contextvars import Token
    from typing import Protocol, overload

    from faststream.broker.message import StreamMessage

    class WrapperProtocol(Generic[MsgType], Protocol):
        @overload
        def __call__(
            self,
            func: None = None,
            *,
            filter: Filter["StreamMessage[MsgType]"],
            parser: CustomParser[MsgType, Any],
            decoder: CustomDecoder["StreamMessage[MsgType]"],
            middlewares: Sequence[Callable[[Any], BaseMiddleware]] = (),
            dependencies: Sequence[Depends] = (),
        ) -> Callable[
            [Callable[P_HandlerParams, T_HandlerReturn]],
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        ]:
            ...

        @overload
        def __call__(
            self,
            func: Callable[P_HandlerParams, T_HandlerReturn] = None,
            *,
            filter: Filter["StreamMessage[MsgType]"],
            parser: CustomParser[MsgType, Any],
            decoder: CustomDecoder["StreamMessage[MsgType]"],
            middlewares: Sequence[Callable[[Any], BaseMiddleware]] = (),
            dependencies: Sequence[Depends] = (),
        ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
            ...

        def __call__(
            self,
            func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
            *,
            filter: Filter["StreamMessage[MsgType]"],
            parser: CustomParser[MsgType, Any],
            decoder: CustomDecoder["StreamMessage[MsgType]"],
            middlewares: Sequence[Callable[[Any], BaseMiddleware]] = (),
            dependencies: Sequence[Depends] = (),
        ) -> Union[
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            Callable[
                [Callable[P_HandlerParams, T_HandlerReturn]],
                HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            ],
        ]:
            ...


@dataclass(slots=True)
class HandlerItem(Generic[MsgType]):
    """A class representing handler overloaded item."""

    handler: HandlerCallWrapper[MsgType, Any, SendableMessage]
    filter: Callable[["StreamMessage[MsgType]"], Awaitable[bool]]
    parser: AsyncParser[MsgType, Any]
    decoder: AsyncDecoder["StreamMessage[MsgType]"]
    middlewares: Sequence[Callable[[Any], BaseMiddleware]]
    dependant: CallModel[Any, SendableMessage]

    @property
    def call_name(self) -> str:
        """Returns the name of the original call."""
        if self.handler is None:
            return ""

        caller = unwrap(self.handler._original_call)
        name = getattr(caller, "__name__", str(caller))
        return name

    @property
    def description(self) -> Optional[str]:
        """Returns the description of original call."""
        if self.handler is None:
            return None

        caller = unwrap(self.handler._original_call)
        description = getattr(caller, "__doc__", None)
        return description


class BaseHandler(AsyncAPIOperation, Generic[MsgType]):
    """A class representing an asynchronous handler.

    Methods:
        add_call : adds a new call to the list of calls
        consume : consumes a message and returns a sendable message
        start : starts the handler
        close : closes the handler
    """

    calls: List[HandlerItem[MsgType]]

    def __init__(
        self,
        *,
        log_context_builder: Callable[["StreamMessage[Any]"], Dict[str, str]],
        middlewares: Sequence[Callable[[MsgType], BaseMiddleware]],
        logger: Optional[Logger],
        description: Optional[str],
        title: Optional[str],
        include_in_schema: bool,
        graceful_timeout: Optional[float],
    ) -> None:
        """Initialize a new instance of the class."""
        self.calls = []
        self.middlewares = middlewares

        self.log_context_builder = log_context_builder
        self.logger = logger
        self.running = False

        self.lock = MultiLock()
        self.graceful_timeout = graceful_timeout

        # AsyncAPI information
        self._description = description
        self._title = title
        super().__init__(include_in_schema=include_in_schema)

    def add_call(
        self,
        filter_: Filter["StreamMessage[MsgType]"],
        parser_: CustomParser[MsgType, Any],
        decoder_: CustomDecoder["StreamMessage[MsgType]"],
        middlewares_: Sequence[Callable[[Any], BaseMiddleware]],
        dependencies_: Sequence[Depends],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[MsgType]":
        def wrapper(
            func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
            *,
            filter: Filter["StreamMessage[MsgType]"] = filter_,
            parser: CustomParser[MsgType, Any] = parser_,
            decoder: CustomDecoder["StreamMessage[MsgType]"] = decoder_,
            middlewares: Sequence[Callable[[Any], BaseMiddleware]] = (),
            dependencies: Sequence[Depends] = (),
        ) -> Union[
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            Callable[
                [Callable[P_HandlerParams, T_HandlerReturn]],
                HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            ],
        ]:
            def real_wrapper(
                func: Callable[P_HandlerParams, T_HandlerReturn],
            ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
                handler, dependant = self.wrap_handler(
                    func=func,
                    dependencies=(*dependencies_, *dependencies),
                    **wrap_kwargs,
                )

                self.calls.append(
                    HandlerItem(
                        handler=handler,
                        dependant=dependant,
                        filter=to_async(filter),
                        parser=to_async(parser),
                        decoder=to_async(decoder),
                        middlewares=(*middlewares_, *middlewares),
                    )
                )

                return handler

            if func is None:
                return real_wrapper

            else:
                return real_wrapper(func)

        return wrapper

    def wrap_handler(
        self,
        *,
        func: Callable[P_HandlerParams, T_HandlerReturn],
        no_ack: bool,
        is_validate: bool,
        dependencies: Sequence[Depends],
        raw: bool,
        retry: int,
        **process_kwargs: Any,
    ) -> Tuple[
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        CallModel[P_HandlerParams, T_HandlerReturn],
    ]:
        build_dep = partial(
            build_call_model,
            cast=is_validate,
            extra_dependencies=dependencies,
        )

        if isinstance(func, HandlerCallWrapper):
            handler_call, func = func, func._original_call
            if handler_call._wrapped_call is not None:
                return handler_call, build_dep(func)

        else:
            handler_call = HandlerCallWrapper(func)

        f = to_async(func)
        dependant = build_dep(f)

        if not raw:
            f = apply_types(None)(f, dependant)

            f = self._wrap_decode_message(
                func=f,
                params_ln=len(dependant.flat_params),
            )

        f = self._process_message(
            func=f,
            watcher=(
                partial(WatcherContext, watcher=get_watcher(self.logger, retry))  # type: ignore[arg-type]
                if not no_ack
                else fake_context
            ),
            **(process_kwargs or {}),
        )

        f = set_message_context(f)
        handler_call.set_wrapped(f)
        return handler_call, dependant

    def _wrap_decode_message(
        self,
        func: Callable[..., Awaitable[T_HandlerReturn]],
        params_ln: int,
    ) -> Callable[
        ["StreamMessage[MsgType]"],
        Awaitable[T_HandlerReturn],
    ]:
        """Wraps a function to decode a message and pass it as an argument to the wrapped function.

        Args:
            func: The function to be wrapped.
            params_ln: The parameters number to be passed to the wrapped function.

        Returns:
            The wrapped function.
        """

        @wraps(func)
        async def decode_wrapper(message: "StreamMessage[MsgType]") -> T_HandlerReturn:
            """A wrapper function to decode and handle a message.

            Args:
                message : The message to be decoded and handled

            Returns:
                The return value of the handler function
            """
            msg = message.decoded_body

            if params_ln > 1:
                if isinstance(msg, Mapping):
                    return await func(**msg)
                elif isinstance(msg, Sequence):
                    return await func(*msg)
            else:
                return await func(msg)

            raise AssertionError("unreachable")

        return decode_wrapper

    @override
    async def consume(self, msg: MsgType) -> SendableMessage:  # type: ignore[override]
        """Consume a message asynchronously.

        Args:
            msg: The message to be consumed.

        Returns:
            The sendable message.

        Raises:
            StopConsume: If the consumption needs to be stopped.
        """
        result: Optional[WrappedReturn[SendableMessage]] = None
        result_msg: SendableMessage = None

        if not self.running:
            return result_msg

        log_context_tag: Optional["Token[Any]"] = None
        async with AsyncExitStack() as stack:
            stack.enter_context(self.lock)

            stack.enter_context(context.scope("handler_", self))

            gl_middlewares: List[BaseMiddleware] = [
                await stack.enter_async_context(m(msg)) for m in self.middlewares
            ]

            logged = False
            processed = False
            for h in self.calls:
                local_middlewares: List[BaseMiddleware] = [
                    await stack.enter_async_context(m(msg)) for m in h.middlewares
                ]

                all_middlewares = gl_middlewares + local_middlewares

                # TODO: add parser & decoder caches
                message = await h.parser(msg)

                if not logged:  # pragma: no branch
                    log_context_tag = context.set_local(
                        "log_context",
                        self.log_context_builder(message),
                    )

                message.decoded_body = await h.decoder(message)
                message.processed = processed

                if await h.filter(message):
                    assert (  # nosec B101
                        not processed
                    ), "You can't process a message with multiple consumers"

                    try:
                        async with AsyncExitStack() as consume_stack:
                            for m_consume in all_middlewares:
                                message.decoded_body = (
                                    await consume_stack.enter_async_context(
                                        m_consume.consume_scope(message.decoded_body)
                                    )
                                )

                            result = await cast(
                                Awaitable[Optional[WrappedReturn[SendableMessage]]],
                                h.handler.call_wrapped(message),
                            )

                        if result is not None:
                            result_msg, pub_response = result

                            # TODO: suppress all publishing errors and raise them after all publishers will be tried
                            for publisher in (pub_response, *h.handler._publishers):
                                if publisher is not None:
                                    async with AsyncExitStack() as pub_stack:
                                        result_to_send = result_msg

                                        for m_pub in all_middlewares:
                                            result_to_send = (
                                                await pub_stack.enter_async_context(
                                                    m_pub.publish_scope(result_to_send)
                                                )
                                            )

                                        await publisher.publish(
                                            message=result_to_send,
                                            correlation_id=message.correlation_id,
                                        )

                    except StopConsume:
                        await self.close()
                        h.handler.trigger()

                    except HandlerException as e:  # pragma: no cover
                        h.handler.trigger()
                        raise e

                    except Exception as e:
                        h.handler.trigger(error=e)
                        raise e

                    else:
                        h.handler.trigger(result=result[0] if result else None)
                        message.processed = processed = True
                        if IS_OPTIMIZED:  # pragma: no cover
                            break

            assert not self.running or processed, "You have to consume message"  # nosec B101

        if log_context_tag is not None:
            context.reset_local("log_context", log_context_tag)

        return result_msg

    @abstractmethod
    async def start(self) -> None:
        """Start the handler."""
        self.running = True

    @abstractmethod
    async def close(self) -> None:
        """Close the handler.

        Blocks loop up to graceful_timeout seconds.
        """
        self.running = False
        await self.lock.wait_release(self.graceful_timeout)

    @property
    def call_name(self) -> str:
        """Returns the name of the handler call."""
        return to_camelcase(self.calls[0].call_name)

    @property
    def description(self) -> Optional[str]:
        """Returns the description of the handler."""
        if self._description:
            return self._description

        if not self.calls:  # pragma: no cover
            return None

        else:
            return self.calls[0].description

    def get_payloads(self) -> List[Tuple[AnyDict, str]]:
        """Get the payloads of the handler."""
        payloads: List[Tuple[AnyDict, str]] = []

        for h in self.calls:
            body = parse_handler_params(
                h.dependant,
                prefix=f"{self._title or self.call_name}:Message",
            )
            payloads.append(
                (
                    body,
                    to_camelcase(h.call_name),
                )
            )

        return payloads


class MultiLock:
    """A class representing a multi lock."""

    def __init__(self) -> None:
        """Initialize a new instance of the class."""
        self.queue: "asyncio.Queue[None]" = asyncio.Queue()

    def __enter__(self) -> Self:
        """Enter the context."""
        self.queue.put_nowait(None)
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """Exit the context."""
        with suppress(asyncio.QueueEmpty, ValueError):
            self.queue.get_nowait()
            self.queue.task_done()

    @property
    def qsize(self) -> int:
        """Return the size of the queue."""
        return self.queue.qsize()

    @property
    def empty(self) -> bool:
        """Return whether the queue is empty."""
        return self.queue.empty()

    async def wait_release(self, timeout: Optional[float] = None) -> None:
        """Wait for the queue to be released.

        Using for graceful shutdown.
        """
        if timeout:
            with anyio.move_on_after(timeout):
                await self.queue.join()
