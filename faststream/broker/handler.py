import asyncio
from abc import abstractmethod
from contextlib import AsyncExitStack, suppress
from inspect import unwrap
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import anyio
from fast_depends.core import CallModel
from typing_extensions import Self, override

from faststream._compat import IS_OPTIMIZED
from faststream.asyncapi.base import AsyncAPIOperation
from faststream.asyncapi.message import parse_handler_params
from faststream.asyncapi.utils import to_camelcase
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    AsyncDecoder,
    AsyncParser,
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    SyncDecoder,
    SyncParser,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.exceptions import HandlerException, StopConsume
from faststream.types import AnyDict, SendableMessage
from faststream.utils.context.repository import context
from faststream.utils.functions import to_async

if TYPE_CHECKING:
    from contextvars import Token


class BaseHandler(AsyncAPIOperation, Generic[MsgType]):
    """A base handler class for asynchronous API operations.

    Attributes:
        calls : List of tuples representing handler calls, filters, parsers, decoders, middlewares, and dependants.
        global_middlewares : Sequence of global middlewares.

    Methods:
        __init__ : Initializes the BaseHandler object.
        name : Returns the name of the handler.
        call_name : Returns the name of the handler call.
        description : Returns the description of the handler.
        consume : Abstract method to consume a message.

    Note: This class inherits from AsyncAPIOperation and is a generic class with type parameter MsgType.

    """

    calls: Union[
        List[
            Tuple[
                HandlerCallWrapper[MsgType, Any, SendableMessage],  # handler
                Callable[[StreamMessage[MsgType]], bool],  # filter
                SyncParser[MsgType, StreamMessage[MsgType]],  # parser
                SyncDecoder[StreamMessage[MsgType]],  # decoder
                Sequence[Callable[[Any], BaseMiddleware]],  # middlewares
                CallModel[Any, SendableMessage],  # dependant
            ]
        ],
        List[
            Tuple[
                HandlerCallWrapper[MsgType, Any, SendableMessage],  # handler
                Callable[[StreamMessage[MsgType]], Awaitable[bool]],  # filter
                AsyncParser[MsgType, StreamMessage[MsgType]],  # parser
                AsyncDecoder[StreamMessage[MsgType]],  # decoder
                Sequence[Callable[[Any], BaseMiddleware]],  # middlewares
                CallModel[Any, SendableMessage],  # dependant
            ]
        ],
    ]

    global_middlewares: Sequence[Callable[[Any], BaseMiddleware]]

    def __init__(
        self,
        *,
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        description: Optional[str] = None,
        title: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        """Initialize a new instance of the class.

        Args:
            log_context_builder: A callable that builds the log context.
            description: Optional description of the instance.
            title: Optional title of the instance.
            include_in_schema: Whether to include the instance in the schema.

        """
        self.calls = []  # type: ignore[assignment]
        self.global_middlewares = []

        self.log_context_builder = log_context_builder
        self.running = False

        # AsyncAPI information
        self._description = description
        self._title = title
        self.include_in_schema = include_in_schema

    @property
    def call_name(self) -> str:
        """Returns the name of the handler call."""
        caller = unwrap(self.calls[0][0]._original_call)
        name = getattr(caller, "__name__", str(caller))
        return to_camelcase(name)

    @property
    def description(self) -> Optional[str]:
        """Returns the description of the handler."""
        if not self.calls:  # pragma: no cover
            description = None

        else:
            caller = unwrap(self.calls[0][0]._original_call)
            description = getattr(caller, "__doc__", None)

        return self._description or description

    @abstractmethod
    def consume(self, msg: MsgType) -> SendableMessage:
        """Consume a message.

        Args:
            msg: The message to be consumed.

        Returns:
            The sendable message.

        Raises:
            NotImplementedError: If the method is not implemented.

        """
        raise NotImplementedError()

    def get_payloads(self) -> List[Tuple[AnyDict, str]]:
        """Get the payloads of the handler."""
        payloads: List[Tuple[AnyDict, str]] = []

        for h, _, _, _, _, dep in self.calls:
            body = parse_handler_params(
                dep, prefix=f"{self._title or self.call_name}:Message"
            )
            payloads.append((body, to_camelcase(unwrap(h._original_call).__name__)))

        return payloads


class AsyncHandler(BaseHandler[MsgType]):
    """A class representing an asynchronous handler.

    Attributes:
        calls : a list of tuples containing the following information:
            - handler : the handler function
            - filter : a callable that filters the stream message
            - parser : an async parser for the message
            - decoder : an async decoder for the message
            - middlewares : a sequence of middlewares
            - dependant : a call model for the handler

    Methods:
        add_call : adds a new call to the list of calls
        consume : consumes a message and returns a sendable message
        start : starts the handler
        close : closes the handler

    """

    calls: List[
        Tuple[
            HandlerCallWrapper[MsgType, Any, SendableMessage],  # handler
            Callable[[StreamMessage[MsgType]], Awaitable[bool]],  # filter
            AsyncParser[MsgType, Any],  # parser
            AsyncDecoder[StreamMessage[MsgType]],  # decoder
            Sequence[Callable[[Any], BaseMiddleware]],  # middlewares
            CallModel[Any, SendableMessage],  # dependant
        ]
    ]

    def __init__(
        self,
        *,
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        description: Optional[str] = None,
        title: Optional[str] = None,
        include_in_schema: bool = True,
        graceful_timeout: Optional[float] = None,
    ) -> None:
        """Initialize a new instance of the class."""
        super().__init__(
            log_context_builder=log_context_builder,
            description=description,
            title=title,
            include_in_schema=include_in_schema,
        )
        self.lock = MultiLock()
        self.graceful_timeout = graceful_timeout

    def add_call(
        self,
        *,
        handler: HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        parser: CustomParser[MsgType, Any],
        decoder: CustomDecoder[Any],
        dependant: CallModel[P_HandlerParams, T_HandlerReturn],
        filter: Filter[StreamMessage[MsgType]],
        middlewares: Optional[Sequence[Callable[[Any], BaseMiddleware]]],
    ) -> None:
        """Adds a call to the handler.

        Args:
            handler: The handler call wrapper.
            parser: The custom parser.
            decoder: The custom decoder.
            dependant: The call model.
            filter: The filter for stream messages.
            middlewares: Optional sequence of middlewares.

        Returns:
            None

        """
        self.calls.append(
            (
                handler,
                to_async(filter),
                to_async(parser) if parser else None,  # type: ignore[arg-type]
                to_async(decoder) if decoder else None,  # type: ignore[arg-type]
                middlewares or (),
                dependant,
            )
        )

    @override
    async def consume(self, msg: MsgType) -> SendableMessage:  # type: ignore[override]
        """Consume a message asynchronously.

        Args:
            msg: The message to be consumed.

        Returns:
            The sendable message.

        Raises:
            StopConsume: If the consumption needs to be stopped.

        Raises:
            Exception: If an error occurs during consumption.

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
                await stack.enter_async_context(m(msg)) for m in self.global_middlewares
            ]

            logged = False
            processed = False
            for handler, filter_, parser, decoder, middlewares, _ in self.calls:
                local_middlewares: List[BaseMiddleware] = [
                    await stack.enter_async_context(m(msg)) for m in middlewares
                ]

                all_middlewares = gl_middlewares + local_middlewares

                # TODO: add parser & decoder caches
                message = await parser(msg)

                if not logged:  # pragma: no branch
                    log_context_tag = context.set_local(
                        "log_context",
                        self.log_context_builder(message),
                    )

                message.decoded_body = await decoder(message)
                message.processed = processed

                if await filter_(message):
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
                                handler.call_wrapped(message),
                            )

                        if result is not None:
                            result_msg, pub_response = result

                            # TODO: suppress all publishing errors and raise them after all publishers will be tried
                            for publisher in (pub_response, *handler._publishers):
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
                        handler.trigger()

                    except HandlerException as e:  # pragma: no cover
                        handler.trigger()
                        raise e

                    except Exception as e:
                        handler.trigger(error=e)
                        raise e

                    else:
                        handler.trigger(result=result[0] if result else None)
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
        """Close the handler."""
        self.running = False
        await self.lock.wait_release(self.graceful_timeout)


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
        """Wait for the queue to be released."""
        if timeout:
            with anyio.move_on_after(timeout):
                await self.queue.join()
