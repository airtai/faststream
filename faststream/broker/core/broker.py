import logging
import warnings
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from typing_extensions import Annotated, Doc

from faststream._compat import is_test_env
from faststream.broker.core.logging_mixin import LoggingMixin
from faststream.broker.middlewares import CriticalLogMiddleware
from faststream.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    ConnectionType,
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
)
from faststream.broker.utils import change_logger_handlers
from faststream.log import access_logger
from faststream.utils.context.repository import context
from faststream.utils.functions import get_function_positional_arguments, to_async

if TYPE_CHECKING:
    from types import TracebackType

    from fast_depends.dependencies import Depends
    from typing_extensions import Self

    from faststream.asyncapi.schema import Tag, TagDict
    from faststream.broker.core.handler import BaseHandler
    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.core.publisher import BasePublisher
    from faststream.broker.message import StreamMessage
    from faststream.broker.middlewares import BaseMiddleware
    from faststream.broker.router import BrokerRouter
    from faststream.security import BaseSecurity
    from faststream.types import AnyDict, SendableMessage


async def default_filter(msg: "StreamMessage[Any]") -> bool:
    """A function to filter stream messages.

    Args:
        msg : A stream message object

    Returns:
        True if the message has not been processed, False otherwise
    """
    return not msg.processed


class BrokerUsecase(
    ABC,
    Generic[MsgType, ConnectionType],
    LoggingMixin,
):
    """A class representing a broker async use case.

    Attributes:
        handlers : A dictionary of handlers for different message types.
        middlewares : A sequence of middleware functions.
        _global_parser : An optional global parser for messages.
        _global_decoder : An optional global decoder for messages.
    """

    handlers: Mapping[Any, "BaseHandler[MsgType]"]
    _publishers: Mapping[Any, "BasePublisher[MsgType]"]
    middlewares: Sequence[Callable[[Any], "BaseMiddleware"]]

    def __init__(
        self,
        url: Annotated[
            Union[str, List[str], None],
            Doc("Broker address to connect"),
        ],
        *args: Any,
        apply_types: Annotated[
            bool,
            Doc("Whether to use FastDepends or not"),
        ] = True,
        validate: Annotated[
            bool,
            Doc("Whether to cast types using Pydantic validation"),
        ] = True,
        logger: Annotated[
            Optional[logging.Logger],
            Doc("Logger object for logging"),
        ] = access_logger,
        log_level: Annotated[
            int,
            Doc("Log level for logging"),
        ] = logging.INFO,
        log_fmt: Annotated[
            Optional[str],
            Doc("Log format for logging"),
        ] = "%(asctime)s %(levelname)s - %(message)s",
        decoder: Annotated[
            Optional[CustomDecoder["StreamMessage[MsgType]"]],
            Doc("Custom decoder object"),
        ] = None,
        parser: Annotated[
            Optional[CustomParser[MsgType, "StreamMessage[MsgType]"]],
            Doc("Custom parser object"),
        ] = None,
        dependencies: Annotated[
            Sequence["Depends"],
            Doc("Dependencies to apply to all broker subscribers"),
        ] = (),
        middlewares: Annotated[
            Sequence[Callable[[Any], "BaseMiddleware"]],
            Doc("Middlewares to apply to all broker publishers/subscribers"),
        ] = (),
        graceful_timeout: Annotated[
            Optional[float],
            Doc("Graceful shutdown timeout"),
        ] = None,
        # AsyncAPI kwargs
        protocol: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol"),
        ] = None,
        protocol_version: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol version"),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc("AsyncAPI server description"),
        ] = None,
        tags: Annotated[
            Optional[Sequence[Union["Tag", "TagDict"]]],
            Doc("AsyncAPI server tags"),
        ] = None,
        asyncapi_url: Annotated[
            Union[str, List[str], None],
            Doc("AsyncAPI hardcoded server addresses"),
        ] = None,
        security: Annotated[
            Optional["BaseSecurity"],
            Doc(
                "Security options to connect broker and generate AsyncAPI server security"
            ),
        ] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the class."""
        super().__init__(
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
        )

        context.set_global("logger", logger)
        context.set_global("broker", self)

        self._connection_args = (url, *args)
        self._connection_kwargs = kwargs

        self.running = False
        self.graceful_timeout = graceful_timeout
        self._connection = None
        self._is_apply_types = apply_types
        self._is_validate = validate

        self.handlers = {}
        self._publishers = {}

        if not is_test_env():
            self.middlewares = (CriticalLogMiddleware(logger, log_level), *middlewares)
        else:
            self.middlewares = middlewares

        self.dependencies = dependencies

        self._global_parser = cast(
            Optional[AsyncCustomParser[MsgType, "StreamMessage[MsgType]"]],
            to_async(parser) if parser else None,
        )
        self._global_decoder = cast(
            Optional[AsyncCustomDecoder["StreamMessage[MsgType]"]],
            to_async(decoder) if decoder else None,
        )

        # AsyncAPI information
        self.url = asyncapi_url or url
        self.protocol = protocol
        self.protocol_version = protocol_version
        self.description = description
        self.tags = tags
        self.security = security

    def include_router(self, router: "BrokerRouter[Any, MsgType]") -> None:
        """Includes a router in the current object.

        Args:
            router: The router to be included.

        Returns:
            None
        """
        for r in router._handlers:
            self.subscriber(*r.args, **r.kwargs)(r.call)

        self._publishers = {**self._publishers, **router._publishers}

    def include_routers(self, *routers: "BrokerRouter[Any, MsgType]") -> None:
        """Includes routers in the current object.

        Args:
            *routers: Variable length argument list of routers to include.

        Returns:
            None
        """
        for r in routers:
            self.include_router(r)

    async def __aenter__(self) -> "Self":
        """Enter the context manager."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exec_tb: Optional["TracebackType"],
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
        if not self.running:
            self.running = True

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

    def _resolve_connection_kwargs(self, *args: Any, **kwargs: Any) -> "AnyDict":
        """Resolve connection keyword arguments.

        Args:
            *args: Positional arguments passed to the function.
            **kwargs: Keyword arguments passed to the function.

        Returns:
            A dictionary containing the resolved connection keyword arguments.
        """
        arguments = get_function_positional_arguments(self.__init__)
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
        """
        raise NotImplementedError()

    async def close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional["TracebackType"] = None,
    ) -> None:
        """Closes the object.

        Args:
            exc_type: The type of the exception being handled, if any.
            exc_val: The exception instance being handled, if any.
            exec_tb: The traceback of the exception being handled, if any.

        Returns:
            None
        """
        self.running = False

        for h in self.handlers.values():
            await h.close()

        if self._connection is not None:
            self._connection = None

    @abstractmethod
    async def publish(
        self,
        message: "SendableMessage",
        *args: Any,
        reply_to: str = "",
        rpc: bool = False,
        rpc_timeout: Optional[float] = None,
        raise_timeout: bool = False,
        **kwargs: Any,
    ) -> Any:
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
    def subscriber(
        self,
        *broker_args: Any,
        filter: Filter["StreamMessage[MsgType]"] = default_filter,
        decoder: Optional[CustomDecoder["StreamMessage[MsgType]"]] = None,
        parser: Optional[CustomParser[MsgType, "StreamMessage[MsgType]"]] = None,
        dependencies: Sequence["Depends"] = (),
        middlewares: Sequence["BaseMiddleware"] = (),
        raw: bool = False,
        no_ack: bool = False,
        retry: Union[bool, int] = False,
        **broker_kwargs: Any,
    ) -> "WrapperProtocol[MsgType]":
        """A function decorator for subscribing to a message broker.

        Args:
            *broker_args: Positional arguments to be passed to the message broker.
            retry: Whether to retry the subscription if it fails. Can be a boolean or an integer specifying the number of retries.
            dependencies: Sequence of dependencies to be injected into the decorated function.
            decoder: Custom decoder function for decoding the message.
            parser: Custom parser function for parsing the decoded message.
            middlewares: Sequence of middleware functions to be applied to the message.
            filter: Filter function for filtering the messages to be processed.
            no_ack: Disable FastStream acknowledgement behavior.
            raw: Whether to return the raw message instead of the processed result.
            get_dependant: Optional argument to get the dependant object.
            **broker_kwargs: Keyword arguments to be passed to the message broker.

        Returns:
            A callable decorator that wraps the decorated function and handles the subscription.
        """
        if self.running and not is_test_env():  # pragma: no cover
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
        publisher: "BasePublisher[MsgType]",
    ) -> "BasePublisher[MsgType]":
        """Publishes a publisher.

        Args:
            key: The key associated with the publisher.
            publisher: The publisher to be published.

        Returns:
            The published publisher.
        """
        self._publishers = {**self._publishers, key: publisher}
        return publisher
