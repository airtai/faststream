import dataclasses
from abc import abstractmethod
from contextlib import AsyncExitStack, asynccontextmanager
from inspect import unwrap
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    cast,
    overload,
)

from faststream.asyncapi.base import AsyncAPIOperation
from faststream.asyncapi.message import parse_handler_params
from faststream.asyncapi.utils import to_camelcase
from faststream.broker.core.handler_wrapper_mixin import WrapHandlerMixin
from faststream.broker.types import (
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.utils import MultiLock
from faststream.exceptions import HandlerException, StopConsume
from faststream.types import AnyDict
from faststream.utils.context.repository import context
from faststream.utils.functions import to_async

if TYPE_CHECKING:
    from types import TracebackType

    from fast_depends.core import CallModel
    from fast_depends.dependencies import Depends
    from typing_extensions import Unpack

    from faststream.broker.core.call_wrapper import HandlerCallWrapper
    from faststream.broker.core.handler_wrapper_mixin import (
        WrapExtraKwargs,
        WrapperProtocol,
    )
    from faststream.broker.message import StreamMessage
    from faststream.broker.middlewares import BaseMiddleware
    from faststream.broker.types import (
        AsyncDecoder,
        AsyncFilter,
        AsyncParser,
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherProtocol,
        SubscriberMiddleware,
    )


@dataclasses.dataclass(slots=True)
class HandlerItem(Generic[MsgType]):
    """A class representing handler overloaded item."""

    handler: "HandlerCallWrapper[MsgType, ..., Any]"
    filter: "AsyncFilter[StreamMessage[MsgType]]"
    parser: "AsyncParser[MsgType]"
    decoder: "AsyncDecoder[StreamMessage[MsgType]]"
    middlewares: Iterable["SubscriberMiddleware"]
    dependent: "CallModel[..., Any]"

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

    async def is_suitable(
        self,
        msg: MsgType,
        cache: Dict[Any, Any],
    ) -> Optional["StreamMessage[MsgType]"]:
        message = cache[self.parser] = cast(
            "StreamMessage[MsgType]",
            cache.get(
                self.parser,
                await self.parser(msg),
            ),
        )

        message.decoded_body = cache[self.decoder] = cache.get(
            self.decoder,
            await self.decoder(message),
        )

        if await self.filter(message):
            return message

        return None

    async def call(
        self,
        message: "StreamMessage[MsgType]",
        extra_middlewares: Iterable["SubscriberMiddleware"],
    ) -> Any:
        async with AsyncExitStack() as consume_stack:
            for middleware in chain(self.middlewares, extra_middlewares):
                message.decoded_body = await consume_stack.enter_async_context(
                    middleware(message.decoded_body)
                )

            try:
                result = await self.handler.call_wrapped(message)

            except StopConsume:
                self.handler.trigger()
                raise

            except HandlerException:
                self.handler.trigger()
                raise

            except Exception as e:
                self.handler.trigger(error=e)
                raise e

            else:
                self.handler.trigger(result=result)
                return result


class BaseHandler(AsyncAPIOperation, WrapHandlerMixin[MsgType]):
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
        middlewares: Iterable["BrokerMiddleware[MsgType]"],
        graceful_timeout: Optional[float],
        watcher: Callable[..., AsyncContextManager[None]],
        extra_context: Optional[AnyDict],
        # AsyncAPI information
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        """Initialize a new instance of the class."""
        self.calls = []
        self.middlewares = middlewares

        self.running = False

        self.producer = None
        self.lock = MultiLock()
        self.watcher = watcher
        self.extra_context = extra_context or {}
        self.graceful_timeout = graceful_timeout
        self.extra_watcher_options = {}

        # AsyncAPI information
        super().__init__(
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    @abstractmethod
    async def start(
        self,
        producer: Optional["PublisherProtocol"],
    ) -> None:
        """Start the handler."""
        self.running = True
        self.producer = producer

    @abstractmethod
    async def close(self) -> None:
        """Close the handler.

        Blocks loop up to graceful_timeout seconds.
        """
        self.running = False
        await self.lock.wait_release(self.graceful_timeout)

    @asynccontextmanager
    async def stop_scope(self) -> AsyncIterator[None]:
        try:
            yield
        except StopConsume:
            await self.close()

    def add_call(
        self,
        *,
        filter_: "Filter[StreamMessage[MsgType]]",
        parser_: "CustomParser[MsgType]",
        decoder_: "CustomDecoder[StreamMessage[MsgType]]",
        middlewares_: Iterable["SubscriberMiddleware"],
        dependencies_: Sequence["Depends"],
        **wrapper_kwargs: "Unpack[WrapExtraKwargs]",
    ) -> "WrapperProtocol[MsgType]":
        # TODO: should return self

        @overload
        def outer_wrapper(
            func: None = None,
            *,
            filter: Optional["Filter[StreamMessage[MsgType]]"] = None,
            parser: Optional["CustomParser[MsgType]"] = None,
            decoder: Optional["CustomDecoder[StreamMessage[MsgType]]"] = None,
            middlewares: Iterable["SubscriberMiddleware"] = (),
            dependencies: Sequence["Depends"] = (),
        ) -> Callable[
            [Callable[P_HandlerParams, T_HandlerReturn]],
            "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
        ]:
            ...

        @overload
        def outer_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
            *,
            filter: Optional["Filter[StreamMessage[MsgType]]"] = None,
            parser: Optional["CustomParser[MsgType]"] = None,
            decoder: Optional["CustomDecoder[StreamMessage[MsgType]]"] = None,
            middlewares: Iterable["SubscriberMiddleware"] = (),
            dependencies: Sequence["Depends"] = (),
        ) -> "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]":
            ...

        def outer_wrapper(
            func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
            *,
            filter: Optional["Filter[StreamMessage[MsgType]]"] = None,
            parser: Optional["CustomParser[MsgType]"] = None,
            decoder: Optional["CustomDecoder[StreamMessage[MsgType]]"] = None,
            middlewares: Iterable["SubscriberMiddleware"] = (),
            dependencies: Sequence["Depends"] = (),
        ) -> Any:
            total_deps = (*dependencies_, *dependencies)
            total_middlewares = (*middlewares_, *middlewares)

            def real_wrapper(
                func: Callable[P_HandlerParams, T_HandlerReturn],
            ) -> "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]":
                handler, dependent = self.wrap_handler(
                    func=func,
                    dependencies=total_deps,
                    **wrapper_kwargs,
                )

                self.calls.append(
                    HandlerItem[MsgType](
                        handler=handler,
                        dependent=dependent,
                        filter=to_async(filter or filter_),
                        parser=cast(
                            "AsyncParser[MsgType]",
                            to_async(parser or parser_),
                        ),
                        decoder=cast(
                            "AsyncDecoder[StreamMessage[MsgType]]",
                            to_async(decoder or decoder_),
                        ),
                        middlewares=total_middlewares,
                    )
                )

                return handler

            if func is None:
                return real_wrapper

            else:
                return real_wrapper(func)

        return outer_wrapper

    async def consume(self, msg: MsgType) -> Any:
        """Consume a message asynchronously.

        Args:
            msg: The message to be consumed.

        Returns:
            The sendable message.
        """
        if not self.running:
            return None

        async with AsyncExitStack() as stack:
            for k, v in self.extra_context.items():
                stack.enter_context(context.scope(k, v))

            stack.enter_context(self.lock)
            stack.enter_context(context.scope("handler_", self))
            # Stop handler at StopConsume exception
            await stack.enter_async_context(self.stop_scope())

            # enter all with raw middlewares
            middlewares: List["BaseMiddleware"] = []
            for m in self.middlewares:
                middleware = m(msg)
                middlewares.append(middleware)
                await middleware.__aenter__()

            cache: Dict[Any, Any] = {}
            for h in self.calls:
                if (message := await h.is_suitable(msg, cache)) is not None:
                    # Acknowledgement scope
                    await stack.enter_async_context(
                        self.watcher(message, **self.extra_watcher_options)
                    )

                    stack.enter_context(
                        context.scope("log_context", self.get_log_context(message))
                    )
                    stack.enter_context(context.scope("message", message))

                    # Middlewares should be exited before log_context scope release
                    @stack.push_async_exit
                    async def close_middlewares(
                        exc_type: Optional[Type[BaseException]] = None,
                        exc_val: Optional[BaseException] = None,
                        exc_tb: Optional["TracebackType"] = None,
                    ) -> None:
                        for m in middlewares:
                            await m.__aexit__(exc_type, exc_val, exc_tb)

                    result_msg = await h.call(
                        message=message,
                        # consumer middlewares
                        extra_middlewares=(m.consume_scope for m in middlewares),
                    )

                    for p in chain(
                        self.make_response_publisher(message),
                        h.handler._publishers,
                    ):
                        await p.publish(
                            message=result_msg,
                            correlation_id=message.correlation_id,
                            # publisher middlewares
                            extra_middlewares=(m.publish_scope for m in middlewares),
                        )

                    return result_msg

            # Suitable handler is not founded
            @stack.push_async_exit
            async def close_middlewares(
                exc_type: Optional[Type[BaseException]] = None,
                exc_val: Optional[BaseException] = None,
                exc_tb: Optional["TracebackType"] = None,
            ) -> None:
                for m in middlewares:
                    await m.__aexit__(exc_type, exc_val, exc_tb)

            raise AssertionError(f"There is no suitable handler for {msg=}")

        return None

    def make_response_publisher(
        self, message: "StreamMessage[MsgType]"
    ) -> Sequence["PublisherProtocol"]:
        raise NotImplementedError()

    def get_log_context(
        self,
        message: Optional["StreamMessage[MsgType]"],
    ) -> Dict[str, str]:
        return {
            "message_id": message.message_id if message else "",
        }

    # AsyncAPI methods

    @property
    def call_name(self) -> str:
        """Returns the name of the handler call."""
        return to_camelcase(self.calls[0].call_name)

    def get_description(self) -> Optional[str]:
        """Returns the description of the handler."""
        if not self.calls:  # pragma: no cover
            return None

        else:
            return self.calls[0].description

    def get_payloads(self) -> List[Tuple[AnyDict, str]]:
        """Get the payloads of the handler."""
        payloads: List[Tuple[AnyDict, str]] = []

        for h in self.calls:
            body = parse_handler_params(
                h.dependent,
                prefix=f"{self.title_ or self.call_name}:Message",
            )

            payloads.append((body, to_camelcase(h.call_name)))

        return payloads
