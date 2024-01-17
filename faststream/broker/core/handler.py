from abc import abstractmethod
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from inspect import unwrap
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from faststream.asyncapi.base import AsyncAPIOperation
from faststream.asyncapi.message import parse_handler_params
from faststream.asyncapi.utils import to_camelcase
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.core.handler_wrapper_mixin import WrapHandlerMixin
from faststream.broker.types import (
    AsyncDecoder,
    AsyncParser,
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    PublisherProtocol,
    T_HandlerReturn,
)
from faststream.broker.utils import MultiLock
from faststream.exceptions import HandlerException, StopConsume
from faststream.types import AnyDict, SendableMessage
from faststream.utils.context.repository import context
from faststream.utils.functions import to_async

if TYPE_CHECKING:
    from types import TracebackType

    from fast_depends.core import CallModel
    from fast_depends.dependencies import Depends

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage
    from faststream.broker.middlewares import BaseMiddleware
    from faststream.broker.types import BrokerMiddleware, SubscriberMiddleware


@dataclass(slots=True)
class HandlerItem(Generic[MsgType]):
    """A class representing handler overloaded item."""

    handler: HandlerCallWrapper[MsgType, Any, SendableMessage]
    filter: Callable[["StreamMessage[MsgType]"], Awaitable[bool]]
    parser: AsyncParser[MsgType, Any]
    decoder: AsyncDecoder["StreamMessage[MsgType]"]
    middlewares: Iterable["SubscriberMiddleware"]
    dependant: "CallModel[Any, SendableMessage]"

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
        message = cache[self.parser] = cache.get(
            self.parser,
            await self.parser(msg),
        )
        message.decoded_body = cache[self.decoder] = cache.get(
            self.decoder,
            await self.decoder(message),
        )

        if await self.filter(message):
            return message

    async def call(
        self,
        message: "StreamMessage[MsgType]",
        extra_middlewares: Iterable["SubscriberMiddleware"],
    ) -> Optional[SendableMessage]:
        result: SendableMessage = None
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
        description: Optional[str],
        title: Optional[str],
        include_in_schema: bool,
        graceful_timeout: Optional[float],
        watcher: Callable[..., AsyncContextManager[None]],
        extra_context: Optional[AnyDict],
    ) -> None:
        """Initialize a new instance of the class."""
        self.calls = []
        self.middlewares = middlewares

        self.running = False

        self.lock = MultiLock()
        self.watcher = watcher
        self.extra_context = extra_context or {}
        self.graceful_timeout = graceful_timeout

        # AsyncAPI information
        self._description = description
        self._title = title
        super().__init__(include_in_schema=include_in_schema)

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

    @asynccontextmanager
    async def stop_scope(self) -> AsyncIterator[None]:
        try:
            yield
        except StopConsume:
            await self.close()

    def add_call(
        self,
        filter_: Filter["StreamMessage[MsgType]"],
        parser_: CustomParser[MsgType, Any],
        decoder_: CustomDecoder["StreamMessage[MsgType]"],
        middlewares_: Iterable["SubscriberMiddleware"],
        dependencies_: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[MsgType]":
        # TODO: should return SELF?
        def wrapper(
            func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
            *,
            filter: Filter["StreamMessage[MsgType]"] = filter_,
            parser: CustomParser[MsgType, Any] = parser_,
            decoder: CustomDecoder["StreamMessage[MsgType]"] = decoder_,
            middlewares: Iterable["SubscriberMiddleware"] = (),
            dependencies: Sequence["Depends"] = (),
        ) -> Union[
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            Callable[
                [Callable[P_HandlerParams, T_HandlerReturn]],
                HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            ],
        ]:
            total_deps = (*dependencies_, *dependencies)
            total_middlewares = (*middlewares_, *middlewares)

            def real_wrapper(
                func: Callable[P_HandlerParams, T_HandlerReturn],
            ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
                handler, dependant = self.wrap_handler(
                    func=func,
                    dependencies=total_deps,
                    **wrap_kwargs,
                )

                self.calls.append(
                    HandlerItem(
                        handler=handler,
                        dependant=dependant,
                        filter=to_async(filter),
                        parser=to_async(parser),
                        decoder=to_async(decoder),
                        middlewares=total_middlewares,
                    )
                )

                return handler

            if func is None:
                return real_wrapper

            else:
                return real_wrapper(func)

        return wrapper

    async def consume(self, msg: MsgType) -> SendableMessage:
        """Consume a message asynchronously.

        Args:
            msg: The message to be consumed.

        Returns:
            The sendable message.
        """
        result_msg: Optional[SendableMessage] = None

        if not self.running:
            return result_msg

        async with AsyncExitStack() as stack:
            for k, v in self.extra_context.items():
                stack.enter_context(context.scope(k, v))

            stack.enter_context(self.lock)
            stack.enter_context(context.scope("handler_", self))
            await stack.enter_async_context(self.stop_scope())

            # enter all middlewares
            middlewares: List["BaseMiddleware"] = []
            for m in self.middlewares:
                middleware = m(msg)
                middlewares.append(middleware)
                await middleware.__aenter__()

            cache = {}
            for h in self.calls:
                if (message := await h.is_suitable(msg, cache)) is not None:
                    await stack.enter_async_context(self.watcher(message))
                    stack.enter_context(
                        context.scope(
                            "log_context",
                            self.get_log_context(message),
                        )
                    )
                    stack.enter_context(context.scope("message", message))

                    # middlewares should be exited before scope does
                    @stack.push_async_callback
                    async def close_middlewares(
                        exc_type: Optional[Type[BaseException]] = None,
                        exc_val: Optional[BaseException] = None,
                        exec_tb: Optional["TracebackType"] = None,
                    ) -> None:
                        for m in middlewares:
                            await m.__aexit__(exc_type, exc_val, exec_tb)

                    result_msg = await h.call(
                        message, (m.consume_scope for m in middlewares)
                    )

                    # TODO: suppress all publishing errors and raise them after all publishers will be tried
                    for p in chain(
                        self.make_response_publisher(message),
                        h.handler._publishers,
                    ):
                        await p.publish(
                            message=result_msg,
                            correlation_id=message.correlation_id,
                            extra_middlewares=(m.publish_scope for m in middlewares),
                        )

                    return result_msg

            raise AssertionError(f"Where is not suitable handler for {msg=}")

    def make_response_publisher(
        self, message: "StreamMessage[MsgType]"
    ) -> Sequence[PublisherProtocol]:
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
