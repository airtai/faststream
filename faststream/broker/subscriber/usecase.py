from abc import abstractmethod
from contextlib import AsyncExitStack, asynccontextmanager
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    ContextManager,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
    overload,
)

from typing_extensions import Self, override

from faststream.asyncapi.abc import AsyncAPIOperation
from faststream.asyncapi.message import parse_handler_params
from faststream.asyncapi.utils import to_camelcase
from faststream.broker.publisher.proto import ProducerProto
from faststream.broker.subscriber.call_item import HandlerItem
from faststream.broker.subscriber.proto import SubscriberProto
from faststream.broker.types import (
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.utils import MultiLock, get_watcher_context, resolve_custom_func
from faststream.broker.wrapper.call import HandlerCallWrapper
from faststream.exceptions import SetupError, StopConsume
from faststream.utils.context.repository import context
from faststream.utils.functions import sync_fake_context, to_async

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream.broker.message import StreamMessage
    from faststream.broker.middlewares import BaseMiddleware
    from faststream.broker.types import (
        AsyncCallable,
        BrokerMiddleware,
        CustomCallable,
        Filter,
        SubscriberMiddleware,
    )
    from faststream.types import AnyDict, Decorator, LoggerProto


class _CallOptions:
    __slots__ = (
        "filter",
        "parser",
        "decoder",
        "middlewares",
        "dependencies",
    )

    def __init__(
        self,
        *,
        filter: "Filter[Any]",
        parser: Optional["CustomCallable"],
        decoder: Optional["CustomCallable"],
        middlewares: Iterable["SubscriberMiddleware[Any]"],
        dependencies: Iterable["Depends"],
    ) -> None:
        self.filter = filter
        self.parser = parser
        self.decoder = decoder
        self.middlewares = middlewares
        self.dependencies = dependencies


class SubscriberUsecase(
    AsyncAPIOperation,
    SubscriberProto[MsgType],
):
    """A class representing an asynchronous handler."""

    lock: ContextManager[Any]
    extra_watcher_options: "AnyDict"
    extra_context: "AnyDict"
    graceful_timeout: Optional[float]

    _broker_dependencies: Iterable["Depends"]
    _call_options: Optional["_CallOptions"]

    def __init__(
        self,
        *,
        no_ack: bool,
        retry: Union[bool, int],
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[MsgType]"],
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        # AsyncAPI information
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        """Initialize a new instance of the class."""
        self.calls = []

        self._default_parser = default_parser
        self._default_decoder = default_decoder
        # Watcher args
        self._no_ack = no_ack
        self._retry = retry

        self._call_options = None
        self.running = False
        self.lock = sync_fake_context()

        # Setup in include
        self._broker_dependencies = broker_dependencies
        self._broker_middlewares = broker_middlewares

        # register in setup later
        self._producer = None
        self.graceful_timeout = None
        self.extra_context = {}
        self.extra_watcher_options = {}

        # AsyncAPI
        self.title_ = title_
        self.description_ = description_
        self.include_in_schema = include_in_schema

    def add_middleware(self, middleware: "BrokerMiddleware[MsgType]") -> None:
        self._broker_middlewares = (*self._broker_middlewares, middleware)

    @override
    def setup(  # type: ignore[override]
        self,
        *,
        logger: Optional["LoggerProto"],
        producer: Optional[ProducerProto],
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
        self.lock = MultiLock()

        self._producer = producer
        self.graceful_timeout = graceful_timeout
        self.extra_context = extra_context

        self.watcher = get_watcher_context(logger, self._no_ack, self._retry)

        for call in self.calls:
            if parser := call.item_parser or broker_parser:
                async_parser = resolve_custom_func(
                    to_async(parser), self._default_parser
                )
            else:
                async_parser = self._default_parser

            if decoder := call.item_decoder or broker_decoder:
                async_decoder = resolve_custom_func(
                    to_async(decoder), self._default_decoder
                )
            else:
                async_decoder = self._default_decoder

            call.setup(
                parser=async_parser,
                decoder=async_decoder,
                apply_types=apply_types,
                is_validate=is_validate,
                _get_dependant=_get_dependant,
                _call_decorators=_call_decorators,
                broker_dependencies=self._broker_dependencies,
            )

            call.handler.refresh(with_mock=False)

    @abstractmethod
    async def start(self) -> None:
        """Start the handler."""
        self.running = True

    @abstractmethod
    async def close(self) -> None:
        """Close the handler.

        Blocks event loop up to graceful_timeout seconds.
        """
        self.running = False
        if isinstance(self.lock, MultiLock):
            await self.lock.wait_release(self.graceful_timeout)

    def add_call(
        self,
        *,
        filter_: "Filter[Any]",
        parser_: Optional["CustomCallable"],
        decoder_: Optional["CustomCallable"],
        middlewares_: Iterable["SubscriberMiddleware[Any]"],
        dependencies_: Iterable["Depends"],
    ) -> Self:
        self._call_options = _CallOptions(
            filter=filter_,
            parser=parser_,
            decoder=decoder_,
            middlewares=middlewares_,
            dependencies=dependencies_,
        )
        return self

    @overload
    def __call__(
        self,
        func: None = None,
        *,
        filter: Optional["Filter[Any]"] = None,
        parser: Optional["CustomCallable"] = None,
        decoder: Optional["CustomCallable"] = None,
        middlewares: Iterable["SubscriberMiddleware[Any]"] = (),
        dependencies: Iterable["Depends"] = (),
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
    ]: ...

    @overload
    def __call__(
        self,
        func: Callable[P_HandlerParams, T_HandlerReturn],
        *,
        filter: Optional["Filter[Any]"] = None,
        parser: Optional["CustomCallable"] = None,
        decoder: Optional["CustomCallable"] = None,
        middlewares: Iterable["SubscriberMiddleware[Any]"] = (),
        dependencies: Iterable["Depends"] = (),
    ) -> "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]": ...

    def __call__(
        self,
        func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
        *,
        filter: Optional["Filter[Any]"] = None,
        parser: Optional["CustomCallable"] = None,
        decoder: Optional["CustomCallable"] = None,
        middlewares: Iterable["SubscriberMiddleware[Any]"] = (),
        dependencies: Iterable["Depends"] = (),
    ) -> Any:
        if (options := self._call_options) is None:
            raise SetupError("You can't create subscriber directly.")

        total_deps = (*options.dependencies, *dependencies)
        total_middlewares = (*options.middlewares, *middlewares)

        def real_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]":
            handler = HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn](
                func
            )

            self.calls.append(
                HandlerItem[MsgType](
                    handler=handler,
                    filter=to_async(filter or options.filter),
                    item_parser=parser or options.parser,
                    item_decoder=decoder or options.decoder,
                    item_middlewares=total_middlewares,
                    dependencies=total_deps,
                )
            )

            return handler

        if func is None:
            return real_wrapper

        else:
            return real_wrapper(func)

    async def consume(self, msg: MsgType) -> Any:
        """Consume a message asynchronously."""
        if not self.running:
            return None

        async with AsyncExitStack() as stack:
            stack.enter_context(self.lock)

            # Enter context before middlewares
            for k, v in self.extra_context.items():
                stack.enter_context(context.scope(k, v))

            stack.enter_context(context.scope("handler_", self))
            # Stop handler at StopConsume exception
            await stack.enter_async_context(self._stop_scope())

            # enter all middlewares
            middlewares: List["BaseMiddleware"] = []
            for base_m in self._broker_middlewares:
                middleware = base_m(msg)
                middlewares.append(middleware)
                await middleware.__aenter__()

            cache: Dict[Any, Any] = {}
            for h in self.calls:
                if (message := await h.is_suitable(msg, cache)) is not None:
                    # Acknowledgement scope
                    await stack.enter_async_context(
                        self.watcher(
                            message,
                            **self.extra_watcher_options,
                        )
                    )

                    stack.enter_context(
                        context.scope("log_context", self.get_log_context(message))
                    )
                    stack.enter_context(context.scope("message", message))

                    # Middlewares should be exited before scope release
                    for m in middlewares:
                        stack.push_async_exit(m.__aexit__)

                    result_msg = await h.call(
                        message=message,
                        # consumer middlewares
                        _extra_middlewares=(m.consume_scope for m in middlewares),
                    )

                    for p in chain(
                        self._make_response_publisher(message),
                        h.handler._publishers,
                    ):
                        await p.publish(
                            result_msg,
                            correlation_id=message.correlation_id,
                            # publisher middlewares
                            _extra_middlewares=(m.publish_scope for m in middlewares),
                        )

                    return result_msg

            # Suitable handler is not founded
            for m in middlewares:
                stack.push_async_exit(m.__aexit__)

            raise AssertionError(f"There is no suitable handler for {msg=}")

        return None

    def get_log_context(
        self,
        message: Optional["StreamMessage[MsgType]"],
    ) -> Dict[str, str]:
        """Generate log context."""
        return {
            "message_id": getattr(message, "message_id", ""),
        }

    @asynccontextmanager
    async def _stop_scope(self) -> AsyncIterator[None]:
        try:
            yield
        except StopConsume:
            await self.close()
        except SystemExit:
            await self.close()
            context.get("app").exit()

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

    def get_payloads(self) -> List[Tuple["AnyDict", str]]:
        """Get the payloads of the handler."""
        payloads: List[Tuple["AnyDict", str]] = []

        for h in self.calls:
            if h.dependant is None:
                raise SetupError("You should setup `Handler` at first.")

            body = parse_handler_params(
                h.dependant,
                prefix=f"{self.title_ or self.call_name}:Message",
            )

            payloads.append((body, to_camelcase(h.call_name)))

        return payloads
