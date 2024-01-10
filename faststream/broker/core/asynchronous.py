import logging
import warnings
from abc import abstractmethod
from types import TracebackType
from typing import (
    Any,
    Callable,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from fast_depends.dependencies import Depends
from typing_extensions import Self

from faststream._compat import is_test_env
from faststream.broker.core.abc import BrokerUsecase
from faststream.broker.handler import BaseHandler
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.publisher import BasePublisher
from faststream.broker.router import BrokerRouter
from faststream.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    ConnectionType,
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.utils import change_logger_handlers
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.log import access_logger
from faststream.types import AnyDict, SendableMessage
from faststream.utils.functions import get_function_positional_arguments, to_async


async def default_filter(msg: StreamMessage[Any]) -> bool:
    """A function to filter stream messages.

    Args:
        msg : A stream message object

    Returns:
        True if the message has not been processed, False otherwise

    """
    return not msg.processed


class BrokerAsyncUsecase(BrokerUsecase[MsgType, ConnectionType]):
    """A class representing a broker async use case.

    Attributes:
        handlers : A dictionary of handlers for different message types.
        middlewares : A sequence of middleware functions.
        _global_parser : An optional global parser for messages.
        _global_decoder : An optional global decoder for messages.

    Methods:
        start() : Abstract method to start the broker async use case.
        _connect(**kwargs: Any) : Abstract method to connect to the broker.
        _close(exc_type: Optional[Type[BaseException]] = None, exc_val: Optional[BaseException] = None, exec_tb: Optional[TracebackType] = None) : Abstract method to close the connection to the broker.
        close(exc_type: Optional[Type[BaseException]] = None, exc_val: Optional[BaseException] = None, exec_tb: Optional[TracebackType] = None) : Close the connection to the broker.
        _process_message(func: Callable[[StreamMessage[MsgType]], Awaitable[T_HandlerReturn]], watcher: BaseWatcher) : Abstract method to process a message.
        publish(message: SendableMessage, *args: Any, reply_to: str = "", rpc: bool = False, rpc_timeout: Optional[float]
    """

    handlers: Mapping[Any, BaseHandler[MsgType]]
    middlewares: Sequence[Callable[[MsgType], BaseMiddleware]]
    _global_parser: Optional[AsyncCustomParser[MsgType, StreamMessage[MsgType]]]
    _global_decoder: Optional[AsyncCustomDecoder[StreamMessage[MsgType]]]

    def include_router(self, router: BrokerRouter[Any, MsgType]) -> None:
        """Includes a router in the current object.

        Args:
            router: The router to be included.

        Returns:
            None
        """
        for r in router._handlers:
            self.subscriber(*r.args, **r.kwargs)(r.call)

        self._publishers = {**self._publishers, **router._publishers}

    def include_routers(self, *routers: BrokerRouter[Any, MsgType]) -> None:
        """Includes routers in the current object.

        Args:
            *routers: Variable length argument list of routers to include.

        Returns:
            None
        """
        for r in routers:
            self.include_router(r)

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exec_tb: Optional[TracebackType],
    ) -> None:
        """Exit the context manager.

        Args:
            exc_type: The type of the exception raised, if any.
            exc_val: The exception raised, if any.
            exec_tb: The traceback of the exception raised, if any.

        Returns:
            None

        Overrides:
            This method overrides the __aexit__ method of the base class.
        """
        await self.close(exc_type, exc_val, exec_tb)

    @abstractmethod
    async def start(self) -> None:
        """Start the broker async use case."""
        self._abc_start()
        for h in self.handlers.values():
            for f in h.calls:
                f.handler.refresh(with_mock=False)
        await self.connect()

    def _abc_start(self) -> None:
        if not self.started:
            self.started = True

            if self.logger is not None:
                change_logger_handlers(self.logger, self.fmt)

    async def connect(self, *args: Any, **kwargs: Any) -> ConnectionType:
        """Connect to a remote server.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The connection object.
        """
        if self._connection is None:
            _kwargs = self._resolve_connection_kwargs(*args, **kwargs)
            self._connection = await self._connect(**_kwargs)
        return self._connection

    def _resolve_connection_kwargs(self, *args: Any, **kwargs: Any) -> AnyDict:
        """Resolve connection keyword arguments.

        Args:
            *args: Positional arguments passed to the function.
            **kwargs: Keyword arguments passed to the function.

        Returns:
            A dictionary containing the resolved connection keyword arguments.
        """
        arguments = get_function_positional_arguments(self.__init__)  # type: ignore
        init_kwargs = {
            **self._connection_kwargs,
            **dict(zip(arguments, self._connection_args)),
        }

        connect_kwargs = {
            **kwargs,
            **dict(zip(arguments, args)),
        }
        return {**init_kwargs, **connect_kwargs}

    @abstractmethod
    async def _connect(self, **kwargs: Any) -> ConnectionType:
        """Connect to a resource.

        Args:
            **kwargs: Additional keyword arguments for the connection.

        Returns:
            The connection object.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError()

    async def close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        """Closes the object.

        Args:
            exc_type: The type of the exception being handled, if any.
            exc_val: The exception instance being handled, if any.
            exec_tb: The traceback of the exception being handled, if any.

        Returns:
            None

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        self.started = False

        for h in self.handlers.values():
            await h.close()

        if self._connection is not None:
            self._connection = None

    @abstractmethod
    async def publish(
        self,
        message: SendableMessage,
        *args: Any,
        reply_to: str = "",
        rpc: bool = False,
        rpc_timeout: Optional[float] = None,
        raise_timeout: bool = False,
        **kwargs: Any,
    ) -> Optional[SendableMessage]:
        """Publish a message.

        Args:
            message: The message to be published.
            *args: Additional arguments.
            reply_to: The reply-to address for the message.
            rpc: Whether the message is for RPC.
            rpc_timeout: The timeout for RPC.
            raise_timeout: Whether to raise an exception on timeout.
            **kwargs: Additional keyword arguments.

        Returns:
            The published message.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def subscriber(  # type: ignore[override,return]
        self,
        *broker_args: Any,
        retry: Union[bool, int] = False,
        dependencies: Sequence[Depends] = (),
        decoder: Optional[CustomDecoder[StreamMessage[MsgType]]] = None,
        parser: Optional[CustomParser[MsgType, StreamMessage[MsgType]]] = None,
        middlewares: Optional[Sequence[Callable[[MsgType], BaseMiddleware]]] = None,
        filter: Filter[StreamMessage[MsgType]] = default_filter,
        _raw: bool = False,
        _get_dependant: Optional[Any] = None,
        **broker_kwargs: Any,
    ) -> Callable[
        [
            Union[
                Callable[P_HandlerParams, T_HandlerReturn],
                HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            ]
        ],
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
    ]:
        """A function decorator for subscribing to a message broker.

        Args:
            *broker_args: Positional arguments to be passed to the message broker.
            retry: Whether to retry the subscription if it fails. Can be a boolean or an integer specifying the number of retries.
            dependencies: Sequence of dependencies to be injected into the decorated function.
            decoder: Custom decoder function for decoding the message.
            parser: Custom parser function for parsing the decoded message.
            middlewares: Sequence of middleware functions to be applied to the message.
            filter: Filter function for filtering the messages to be processed.
            _raw: Whether to return the raw message instead of the processed result.
            _get_dependant: Optional argument to get the dependant object.
            **broker_kwargs: Keyword arguments to be passed to the message broker.

        Returns:
            A callable decorator that wraps the decorated function and handles the subscription.

        Raises:
            NotImplementedError: If silent animals are not supported.
        """
        if self.started and not is_test_env():  # pragma: no cover
            warnings.warn(
                "You are trying to register `handler` with already running broker\n"
                "It has no effect until broker restarting.",
                category=RuntimeWarning,
                stacklevel=1,
            )

    @abstractmethod
    def publisher(
        self,
        key: Any,
        publisher: BasePublisher[MsgType],
    ) -> BasePublisher[MsgType]:
        """Publishes a publisher.

        Args:
            key: The key associated with the publisher.
            publisher: The publisher to be published.

        Returns:
            The published publisher.
        """
        self._publishers = {**self._publishers, key: publisher}
        return publisher

    def __init__(
        self,
        *args: Any,
        apply_types: bool = True,
        validate: bool = True,
        logger: Optional[logging.Logger] = access_logger,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = "%(asctime)s %(levelname)s - %(message)s",
        dependencies: Sequence[Depends] = (),
        decoder: Optional[CustomDecoder[StreamMessage[MsgType]]] = None,
        parser: Optional[CustomParser[MsgType, StreamMessage[MsgType]]] = None,
        middlewares: Optional[Sequence[Callable[[MsgType], BaseMiddleware]]] = None,
        graceful_timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the class.

        Args:
            *args: Variable length arguments
            apply_types: Whether to apply types or not
            validate: Whether to cast types using Pydantic validation.
            logger: Logger object for logging
            log_level: Log level for logging
            log_fmt: Log format for logging
            dependencies: Sequence of dependencies
            decoder: Custom decoder object
            parser: Custom parser object
            middlewares: Sequence of middlewares
            graceful_timeout: Graceful timeout
            **kwargs: Keyword arguments
        """
        super().__init__(
            *args,
            apply_types=apply_types,
            validate=validate,
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
            dependencies=dependencies,
            decoder=cast(
                Optional[AsyncCustomDecoder[StreamMessage[MsgType]]],
                to_async(decoder) if decoder else None,
            ),
            parser=cast(
                Optional[AsyncCustomParser[MsgType, StreamMessage[MsgType]]],
                to_async(parser) if parser else None,
            ),
            middlewares=middlewares,
            **kwargs,
        )
        self.graceful_timeout = graceful_timeout
