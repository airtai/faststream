import logging
import warnings
from abc import ABC, abstractmethod
from types import TracebackType
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
)

from fast_depends.dependencies import Depends

from faststream._compat import is_test_env
from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.mixins import LoggingMixin
from faststream.broker.handler import BaseHandler
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware, CriticalLogMiddleware
from faststream.broker.publisher import BasePublisher
from faststream.broker.router import BrokerRouter
from faststream.broker.types import (
    ConnectionType,
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.utils import (
    change_logger_handlers,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.log import access_logger
from faststream.security import BaseSecurity
from faststream.types import AnyDict
from faststream.utils import context
from faststream.utils.functions import (
    get_function_positional_arguments,
)


class BrokerUsecase(
    ABC,
    Generic[MsgType, ConnectionType],
    LoggingMixin,
):
    """A class representing a broker use case.

    Attributes:
        logger : optional logger object
        log_level : log level
        handlers : dictionary of handlers
        _publishers : dictionary of publishers
        dependencies : sequence of dependencies
        started : boolean indicating if the broker has started
        middlewares : sequence of middleware functions
        _global_parser : optional custom parser object
        _global_decoder : optional custom decoder object
        _connection : optional connection object
        _fmt : optional string format

    Methods:
        __init__ : constructor method
        include_router : include a router in the broker
        include_routers : include multiple routers in the broker
        _resolve_connection_kwargs : resolve connection kwargs
        _wrap_handler : wrap a handler function
        _abc_start : start the broker
        _abc_close : close the broker
        _abc__close : close the broker connection
        _process_message : process a message
        subscriber : decorator to register a subscriber
        publisher : register a publisher
        _wrap_decode_message : wrap a message decoding function
    """

    logger: Optional[logging.Logger]
    log_level: int
    handlers: Mapping[Any, BaseHandler[MsgType]]
    _publishers: Mapping[Any, BasePublisher[MsgType]]

    dependencies: Sequence[Depends]
    started: bool
    middlewares: Sequence[Callable[[Any], BaseMiddleware]]
    _global_parser: Optional[CustomParser[MsgType, StreamMessage[MsgType]]]
    _global_decoder: Optional[CustomDecoder[StreamMessage[MsgType]]]
    _connection: Optional[ConnectionType]
    _fmt: Optional[str]

    def __init__(
        self,
        url: Union[str, List[str]],
        *args: Any,
        # AsyncAPI kwargs
        protocol: Optional[str] = None,
        protocol_version: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Sequence[Union[asyncapi.Tag, asyncapi.TagDict]]] = None,
        asyncapi_url: Union[str, List[str], None] = None,
        # broker kwargs
        apply_types: bool = True,
        validate: bool = True,
        logger: Optional[logging.Logger] = access_logger,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = "%(asctime)s %(levelname)s - %(message)s",
        dependencies: Sequence[Depends] = (),
        middlewares: Optional[Sequence[Callable[[MsgType], BaseMiddleware]]] = None,
        decoder: Optional[CustomDecoder[StreamMessage[MsgType]]] = None,
        parser: Optional[CustomParser[MsgType, StreamMessage[MsgType]]] = None,
        security: Optional[BaseSecurity] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a broker.

        Args:
            url: The URL or list of URLs to connect to.
            *args: Additional arguments.
            protocol: The protocol to use for the connection.
            protocol_version: The version of the protocol.
            description: A description of the broker.
            tags: Tags associated with the broker.
            asyncapi_url: The URL or list of URLs to the AsyncAPI schema.
            apply_types: Whether to apply types to messages.
            validate: Whether to cast types using Pydantic validation.
            logger: The logger to use.
            log_level: The log level to use.
            log_fmt: The log format to use.
            dependencies: Dependencies of the broker.
            middlewares: Middlewares to use.
            decoder: Custom decoder for messages.
            parser: Custom parser for messages.
            security: Security scheme to use.
            **kwargs: Additional keyword arguments.

        """
        super().__init__(
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
        )

        self._connection = None
        self._is_apply_types = apply_types
        self._is_validate = validate
        self.handlers = {}
        self._publishers = {}
        empty_middleware: Sequence[Callable[[MsgType], BaseMiddleware]] = ()
        midd_args: Sequence[Callable[[MsgType], BaseMiddleware]] = (
            middlewares or empty_middleware
        )

        if not is_test_env():
            self.middlewares = (CriticalLogMiddleware(logger, log_level), *midd_args)
        else:
            self.middlewares = midd_args

        self.dependencies = dependencies

        self._connection_args = (url, *args)
        self._connection_kwargs = kwargs

        self._global_parser = parser
        self._global_decoder = decoder

        context.set_global("logger", logger)
        context.set_global("broker", self)

        self.started = False

        # AsyncAPI information
        self.url = asyncapi_url or url
        self.protocol = protocol
        self.protocol_version = protocol_version
        self.description = description
        self.tags = tags
        self.security = security

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

    def _abc_start(self) -> None:
        if not self.started:
            self.started = True

            if self.logger is not None:
                change_logger_handlers(self.logger, self.fmt)

    def _abc_close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        """Closes the ABC.

        Args:
            exc_type: The exception type
            exc_val: The exception value
            exec_tb: The traceback

        Returns:
            None
        """
        self.started = False

    def _abc__close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        """Closes the connection.

        Args:
            exc_type: The type of the exception being handled (optional)
            exc_val: The exception instance being handled (optional)
            exec_tb: The traceback for the exception being handled (optional)

        Returns:
            None

        Note:
            This is an abstract method and must be implemented by subclasses.
        """
        self._connection = None

    @abstractmethod
    def subscriber(  # type: ignore[return]
        self,
        *broker_args: Any,
        retry: Union[bool, int] = False,
        dependencies: Sequence[Depends] = (),
        decoder: Optional[CustomDecoder[StreamMessage[MsgType]]] = None,
        parser: Optional[CustomParser[MsgType, StreamMessage[MsgType]]] = None,
        middlewares: Optional[
            Sequence[
                Callable[
                    [StreamMessage[MsgType]],
                    BaseMiddleware,
                ]
            ]
        ] = None,
        filter: Filter[StreamMessage[MsgType]] = lambda m: not m.processed,
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
        """This is a function decorator for subscribing to a message broker.

        Args:
            *broker_args: Positional arguments to be passed to the broker.
            retry: Whether to retry the subscription if it fails. Can be a boolean or an integer specifying the number of retries.
            dependencies: Sequence of dependencies to be injected into the handler function.
            decoder: Custom decoder function to decode the message.
            parser: Custom parser function to parse the decoded message.
            middlewares: Sequence of middleware functions to be applied to the message.
            filter: Filter function to filter the messages to be processed.
            _raw: Whether to return the raw message instead of the processed message.
            _get_dependant: Optional parameter to get the dependant object.
            **broker_kwargs: Keyword arguments to be passed to the broker.

        Returns:
            A callable object that can be used as a decorator for a handler function.

        Raises:
            RuntimeWarning: If the broker is already running.
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
