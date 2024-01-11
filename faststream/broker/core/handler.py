from abc import abstractmethod
from contextlib import AsyncExitStack
from dataclasses import dataclass
from inspect import unwrap
from logging import Logger
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
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
    WrappedReturn,
)
from faststream.broker.utils import MultiLock
from faststream.exceptions import HandlerException, StopConsume
from faststream.types import AnyDict, SendableMessage
from faststream.utils.context.repository import context
from faststream.utils.functions import to_async

if TYPE_CHECKING:
    from fast_depends.core import CallModel
    from fast_depends.dependencies import Depends

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage
    from faststream.broker.middlewares import BaseMiddleware


@dataclass(slots=True)
class HandlerItem(Generic[MsgType]):
    """A class representing handler overloaded item."""

    handler: HandlerCallWrapper[MsgType, Any, SendableMessage]
    filter: Callable[["StreamMessage[MsgType]"], Awaitable[bool]]
    parser: AsyncParser[MsgType, Any]
    decoder: AsyncDecoder["StreamMessage[MsgType]"]
    middlewares: Sequence[Callable[[Any], "BaseMiddleware"]]
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

    async def call(
        self, msg: MsgType, cache: Dict[Any, Any]
    ) -> AsyncGenerator[
        Dict[str, str],
        Optional["StreamMessage[MsgType]"],
    ]:
        message = cache[self.parser] = cache.get(
            self.parser,
            await self.parser(msg),
        )
        message.decoded_body = cache[self.decoder] = cache.get(
            self.decoder,
            await self.decoder(message),
        )

        if await self.filter(message):
            log_context = yield message

            result = None
            async with AsyncExitStack() as consume_stack:
                consume_stack.enter_context(context.scope("message", message))
                consume_stack.enter_context(context.scope("log_context", log_context))

                for middleware in self.middlewares:
                    message.decoded_body = await consume_stack.enter_async_context(
                        middleware.consume_scope(message.decoded_body)
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
                    self.handler.trigger(result=result[0] if result else None)
                    yield result

        else:
            yield None


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
        log_context_builder: Callable[["StreamMessage[Any]"], Dict[str, str]],
        middlewares: Sequence[Callable[[MsgType], "BaseMiddleware"]],
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

    def add_call(
        self,
        filter_: Filter["StreamMessage[MsgType]"],
        parser_: CustomParser[MsgType, Any],
        decoder_: CustomDecoder["StreamMessage[MsgType]"],
        middlewares_: Sequence[Callable[[Any], "BaseMiddleware"]],
        dependencies_: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[MsgType]":
        def wrapper(
            func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
            *,
            filter: Filter["StreamMessage[MsgType]"] = filter_,
            parser: CustomParser[MsgType, Any] = parser_,
            decoder: CustomDecoder["StreamMessage[MsgType]"] = decoder_,
            middlewares: Sequence[Callable[[Any], "BaseMiddleware"]] = (),
            dependencies: Sequence["Depends"] = (),
        ) -> Union[
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            Callable[
                [Callable[P_HandlerParams, T_HandlerReturn]],
                HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            ],
        ]:
            total_deps = (*dependencies_, *dependencies)
            total_middlewares = (*self.middlewares, *middlewares_, *middlewares)

            def real_wrapper(
                func: Callable[P_HandlerParams, T_HandlerReturn],
            ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
                handler, dependant = self.wrap_handler(
                    func=func,
                    dependencies=total_deps,
                    logger=self.logger,
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
        result: Optional[WrappedReturn[SendableMessage]] = None
        result_msg: SendableMessage = None

        if not self.running:
            return result_msg

        async with AsyncExitStack() as stack:
            stack.enter_context(self.lock)

            stack.enter_context(context.scope("handler_", self))

            for m in self.middlewares:
                await stack.enter_async_context(m(msg))

            cache = {}
            processed = False
            for h in self.calls:
                if processed:
                    break

                caller = h.call(msg, cache)

                if (message := await caller.__anext__()) is not None:
                    processed = True
                    try:
                        await caller.asend(self.log_context_builder(message))
                    except StopAsyncIteration as e:
                        result = e.value
                    except StopConsume:
                        await self.close()
                        return

                    # TODO: suppress all publishing errors and raise them after all publishers will be tried
                    for publisher in (
                        *self.make_response_publisher(message),
                        *h.handler._publishers,
                    ):
                        if publisher is not None:
                            async with AsyncExitStack() as pub_stack:
                                for m_pub in h.middlewares:
                                    result = await pub_stack.enter_async_context(
                                        m_pub.publish_scope(result)
                                    )

                                await publisher.publish(
                                    message=result,
                                    correlation_id=message.correlation_id,
                                )

            assert not self.running or processed, "You have to consume message"  # nosec B101

        return result_msg

    def make_response_publisher(
        self, message: "StreamMessage[MsgType]"
    ) -> Sequence[PublisherProtocol]:
        raise NotImplementedError()
