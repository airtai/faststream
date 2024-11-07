from abc import abstractmethod
from collections.abc import Iterable
from contextlib import AbstractContextManager, AsyncExitStack
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    overload,
)

from typing_extensions import Self, override

from faststream._internal.subscriber.call_item import HandlerItem
from faststream._internal.subscriber.call_wrapper.call import HandlerCallWrapper
from faststream._internal.subscriber.proto import SubscriberProto
from faststream._internal.subscriber.utils import (
    MultiLock,
    default_filter,
    resolve_custom_func,
)
from faststream._internal.types import (
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream._internal.utils.functions import sync_fake_context, to_async
from faststream.exceptions import SetupError, StopConsume, SubscriberNotFound
from faststream.middlewares import AckPolicy, AcknowledgementMiddleware
from faststream.response import ensure_response
from faststream.specification.asyncapi.message import parse_handler_params
from faststream.specification.asyncapi.utils import to_camelcase

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant

    from faststream._internal.basic_types import AnyDict, Decorator
    from faststream._internal.context.repository import ContextRepo
    from faststream._internal.publisher.proto import (
        BasePublisherProto,
    )
    from faststream._internal.state import BrokerState, Pointer
    from faststream._internal.types import (
        AsyncCallable,
        BrokerMiddleware,
        CustomCallable,
        Filter,
        SubscriberMiddleware,
    )
    from faststream.message import StreamMessage
    from faststream.middlewares import BaseMiddleware
    from faststream.response import Response


class _CallOptions:
    __slots__ = (
        "decoder",
        "dependencies",
        "middlewares",
        "parser",
    )

    def __init__(
        self,
        *,
        parser: Optional["CustomCallable"],
        decoder: Optional["CustomCallable"],
        middlewares: Iterable["SubscriberMiddleware[Any]"],
        dependencies: Iterable["Dependant"],
    ) -> None:
        self.parser = parser
        self.decoder = decoder
        self.middlewares = middlewares
        self.dependencies = dependencies


class SubscriberUsecase(SubscriberProto[MsgType]):
    """A class representing an asynchronous handler."""

    lock: "AbstractContextManager[Any]"
    extra_watcher_options: "AnyDict"
    extra_context: "AnyDict"
    graceful_timeout: Optional[float]

    _broker_dependencies: Iterable["Dependant"]
    _call_options: Optional["_CallOptions"]
    _call_decorators: Iterable["Decorator"]

    def __init__(
        self,
        *,
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[MsgType]"],
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        ack_policy: AckPolicy,
        # AsyncAPI information
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        """Initialize a new instance of the class."""
        self.calls = []

        self._parser = default_parser
        self._decoder = default_decoder
        self._no_reply = no_reply
        self.ack_policy = ack_policy

        self._call_options = None
        self._call_decorators = ()
        self.running = False
        self.lock = sync_fake_context()

        # Setup in include
        self._broker_dependencies = broker_dependencies
        self._broker_middlewares = broker_middlewares

        # register in setup later
        self.extra_context = {}
        self.extra_watcher_options = {}

        # AsyncAPI
        self.title_ = title_
        self.description_ = description_
        self.include_in_schema = include_in_schema

        if self.ack_policy is not AckPolicy.DO_NOTHING:
            self._broker_middlewares = (
                AcknowledgementMiddleware(
                    self.ack_policy,
                    self.extra_watcher_options,
                ),
                *self._broker_middlewares,
            )

    def add_middleware(self, middleware: "BrokerMiddleware[MsgType]") -> None:
        self._broker_middlewares = (*self._broker_middlewares, middleware)

    @override
    def _setup(  # type: ignore[override]
        self,
        *,
        extra_context: "AnyDict",
        # broker options
        broker_parser: Optional["CustomCallable"],
        broker_decoder: Optional["CustomCallable"],
        # dependant args
        state: "Pointer[BrokerState]",
    ) -> None:
        # TODO: add EmptyBrokerState to init
        self._state = state

        self.extra_context = extra_context

        for call in self.calls:
            if parser := call.item_parser or broker_parser:
                async_parser = resolve_custom_func(to_async(parser), self._parser)
            else:
                async_parser = self._parser

            if decoder := call.item_decoder or broker_decoder:
                async_decoder = resolve_custom_func(to_async(decoder), self._decoder)
            else:
                async_decoder = self._decoder

            self._parser = async_parser
            self._decoder = async_decoder

            call._setup(
                parser=async_parser,
                decoder=async_decoder,
                state=state,
                broker_dependencies=self._broker_dependencies,
                _call_decorators=self._call_decorators,
            )

            call.handler.refresh(with_mock=False)

    @abstractmethod
    async def start(self) -> None:
        """Start the handler."""
        self.lock = MultiLock()

        self.running = True

    @abstractmethod
    async def close(self) -> None:
        """Close the handler.

        Blocks event loop up to graceful_timeout seconds.
        """
        self.running = False
        if isinstance(self.lock, MultiLock):
            await self.lock.wait_release(self._state.get().graceful_timeout)

    def add_call(
        self,
        *,
        parser_: Optional["CustomCallable"],
        decoder_: Optional["CustomCallable"],
        middlewares_: Iterable["SubscriberMiddleware[Any]"],
        dependencies_: Iterable["Dependant"],
    ) -> Self:
        self._call_options = _CallOptions(
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
        filter: "Filter[Any]" = default_filter,
        parser: Optional["CustomCallable"] = None,
        decoder: Optional["CustomCallable"] = None,
        middlewares: Iterable["SubscriberMiddleware[Any]"] = (),
        dependencies: Iterable["Dependant"] = (),
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
    ]: ...

    @overload
    def __call__(
        self,
        func: Callable[P_HandlerParams, T_HandlerReturn],
        *,
        filter: "Filter[Any]" = default_filter,
        parser: Optional["CustomCallable"] = None,
        decoder: Optional["CustomCallable"] = None,
        middlewares: Iterable["SubscriberMiddleware[Any]"] = (),
        dependencies: Iterable["Dependant"] = (),
    ) -> "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]": ...

    def __call__(
        self,
        func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
        *,
        filter: "Filter[Any]" = default_filter,
        parser: Optional["CustomCallable"] = None,
        decoder: Optional["CustomCallable"] = None,
        middlewares: Iterable["SubscriberMiddleware[Any]"] = (),
        dependencies: Iterable["Dependant"] = (),
    ) -> Any:
        if (options := self._call_options) is None:
            msg = (
                "You can't create subscriber directly. Please, use `add_call` at first."
            )
            raise SetupError(
                msg,
            )

        total_deps = (*options.dependencies, *dependencies)
        total_middlewares = (*options.middlewares, *middlewares)
        async_filter = to_async(filter)

        def real_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]":
            handler = HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn](
                func,
            )
            self.calls.append(
                HandlerItem[MsgType](
                    handler=handler,
                    filter=async_filter,
                    item_parser=parser or options.parser,
                    item_decoder=decoder or options.decoder,
                    item_middlewares=total_middlewares,
                    dependencies=total_deps,
                ),
            )

            return handler

        if func is None:
            return real_wrapper

        return real_wrapper(func)

    async def consume(self, msg: MsgType) -> Any:
        """Consume a message asynchronously."""
        if not self.running:
            return None

        try:
            return await self.process_message(msg)

        except StopConsume:
            # Stop handler at StopConsume exception
            await self.close()

        except SystemExit:
            # Stop handler at `exit()` call
            await self.close()

            if app := self._state.get().di_state.context.get("app"):
                app.exit()

        except Exception:  # nosec B110
            # All other exceptions were logged by CriticalLogMiddleware
            pass

    async def process_message(self, msg: MsgType) -> "Response":
        """Execute all message processing stages."""
        broker_state = self._state.get()
        context: ContextRepo = broker_state.di_state.context

        async with AsyncExitStack() as stack:
            stack.enter_context(self.lock)

            # Enter context before middlewares
            stack.enter_context(
                context.scope("logger", broker_state.logger_state.logger.logger)
            )
            for k, v in self.extra_context.items():
                stack.enter_context(context.scope(k, v))

            stack.enter_context(context.scope("handler_", self))

            # enter all middlewares
            middlewares: list[BaseMiddleware] = []
            for base_m in self._broker_middlewares:
                middleware = base_m(msg, context=context)
                middlewares.append(middleware)
                await middleware.__aenter__()

            cache: dict[Any, Any] = {}
            parsing_error: Optional[Exception] = None
            for h in self.calls:
                try:
                    message = await h.is_suitable(msg, cache)
                except Exception as e:
                    parsing_error = e
                    break

                if message is not None:
                    stack.enter_context(
                        context.scope("log_context", self.get_log_context(message)),
                    )
                    stack.enter_context(context.scope("message", message))

                    # Middlewares should be exited before scope release
                    for m in middlewares:
                        stack.push_async_exit(m.__aexit__)

                    result_msg = ensure_response(
                        await h.call(
                            message=message,
                            # consumer middlewares
                            _extra_middlewares=(m.consume_scope for m in middlewares),
                        ),
                    )

                    if not result_msg.correlation_id:
                        result_msg.correlation_id = message.correlation_id

                    for p in chain(
                        self.__get_response_publisher(message),
                        h.handler._publishers,
                    ):
                        await p._publish(
                            result_msg.as_publish_command(),
                            _extra_middlewares=(m.publish_scope for m in middlewares),
                        )

                    # Return data for tests
                    return result_msg

            # Suitable handler was not found or
            # parsing/decoding exception occurred
            for m in middlewares:
                stack.push_async_exit(m.__aexit__)

            if parsing_error:
                raise parsing_error

            msg = f"There is no suitable handler for {msg=}"
            raise SubscriberNotFound(msg)

        # An error was raised and processed by some middleware
        return ensure_response(None)

    def __get_response_publisher(
        self,
        message: "StreamMessage[MsgType]",
    ) -> Iterable["BasePublisherProto"]:
        if not message.reply_to or self._no_reply:
            return ()

        return self._make_response_publisher(message)

    def get_log_context(
        self,
        message: Optional["StreamMessage[MsgType]"],
    ) -> dict[str, str]:
        """Generate log context."""
        return {
            "message_id": getattr(message, "message_id", ""),
        }

    # AsyncAPI methods

    @property
    def call_name(self) -> str:
        """Returns the name of the handler call."""
        if not self.calls:
            return "Subscriber"

        return to_camelcase(self.calls[0].call_name)

    def get_description(self) -> Optional[str]:
        """Returns the description of the handler."""
        if not self.calls:  # pragma: no cover
            return None

        return self.calls[0].description

    def get_payloads(self) -> list[tuple["AnyDict", str]]:
        """Get the payloads of the handler."""
        payloads: list[tuple[AnyDict, str]] = []

        for h in self.calls:
            if h.dependant is None:
                msg = "You should setup `Handler` at first."
                raise SetupError(msg)

            body = parse_handler_params(
                h.dependant,
                prefix=f"{self.title_ or self.call_name}:Message",
            )

            payloads.append((body, to_camelcase(h.call_name)))

        if not self.calls:
            payloads.append(
                (
                    {
                        "title": f"{self.title_ or self.call_name}:Message:Payload",
                    },
                    to_camelcase(self.call_name),
                ),
            )

        return payloads
