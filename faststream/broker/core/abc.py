import logging
from abc import ABC
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Mapping,
    Optional,
    Sequence,
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
from faststream.broker.types import (
    ConnectionType,
    CustomDecoder,
    CustomParser,
    MsgType,
)
from faststream.log import access_logger
from faststream.security import BaseSecurity
from faststream.utils import context


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
