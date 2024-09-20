import logging
from abc import abstractmethod
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from typing_extensions import Annotated, Doc, Self

from faststream._internal._compat import is_test_env
from faststream._internal.log.logging import set_logger_fmt
from faststream._internal.proto import SetupAble
from faststream._internal.subscriber.proto import SubscriberProto
from faststream._internal.subscriber.utils import process_msg
from faststream._internal.types import (
    AsyncCustomCallable,
    BrokerMiddleware,
    ConnectionType,
    CustomCallable,
    MsgType,
)
from faststream._internal.utils.functions import to_async
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.middlewares.logging import CriticalLogMiddleware

from .logging_mixin import LoggingBroker

if TYPE_CHECKING:
    from types import TracebackType

    from fast_depends.dependencies import Depends

    from faststream._internal.basic_types import AnyDict, Decorator, LoggerProto
    from faststream._internal.publisher.proto import (
        ProducerProto,
        PublisherProto,
    )
    from faststream.security import BaseSecurity
    from faststream.specification.schema.tag import Tag, TagDict


class BrokerUsecase(
    LoggingBroker[MsgType],
    SetupAble,
    Generic[MsgType, ConnectionType],
):
    """A class representing a broker async use case."""

    url: Union[str, Sequence[str]]
    _connection: Optional[ConnectionType]
    _producer: Optional["ProducerProto"]

    def __init__(
        self,
        *,
        decoder: Annotated[
            Optional["CustomCallable"],
            Doc("Custom decoder object."),
        ],
        parser: Annotated[
            Optional["CustomCallable"],
            Doc("Custom parser object."),
        ],
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies to apply to all broker subscribers."),
        ],
        middlewares: Annotated[
            Iterable["BrokerMiddleware[MsgType]"],
            Doc("Middlewares to apply to all broker publishers/subscribers."),
        ],
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Graceful shutdown timeout. Broker waits for all running subscribers completion before shut down."
            ),
        ],
        # Logging args
        default_logger: Annotated[
            logging.Logger,
            Doc("Logger object to use if `logger` is not set."),
        ],
        logger: Annotated[
            Optional["LoggerProto"],
            Doc("User specified logger to pass into Context and log service messages."),
        ],
        log_level: Annotated[
            int,
            Doc("Service messages log level."),
        ],
        log_fmt: Annotated[
            Optional[str],
            Doc("Default logger log format."),
        ],
        # FastDepends args
        apply_types: Annotated[
            bool,
            Doc("Whether to use FastDepends or not."),
        ],
        validate: Annotated[
            bool,
            Doc("Whether to cast types using Pydantic validation."),
        ],
        _get_dependant: Annotated[
            Optional[Callable[..., Any]],
            Doc("Custom library dependant generator callback."),
        ],
        _call_decorators: Annotated[
            Iterable["Decorator"],
            Doc("Any custom decorator to apply to wrapped functions."),
        ],
        # AsyncAPI kwargs
        protocol: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol."),
        ],
        protocol_version: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol version."),
        ],
        description: Annotated[
            Optional[str],
            Doc("AsyncAPI server description."),
        ],
        tags: Annotated[
            Optional[Iterable[Union["Tag", "TagDict"]]],
            Doc("AsyncAPI server tags."),
        ],
        specification_url: Annotated[
            Union[str, List[str]],
            Doc("AsyncAPI hardcoded server addresses."),
        ],
        security: Annotated[
            Optional["BaseSecurity"],
            Doc(
                "Security options to connect broker and generate AsyncAPI server security."
            ),
        ],
        **connection_kwargs: Any,
    ) -> None:
        super().__init__(
            middlewares=middlewares,
            dependencies=dependencies,
            decoder=cast(
                Optional["AsyncCustomCallable"],
                to_async(decoder) if decoder else None,
            ),
            parser=cast(
                Optional["AsyncCustomCallable"],
                to_async(parser) if parser else None,
            ),
            # Broker is a root router
            include_in_schema=True,
            prefix="",
            # Logging args
            default_logger=default_logger,
            log_level=log_level,
            log_fmt=log_fmt,
            logger=logger,
        )

        self.running = False
        self.graceful_timeout = graceful_timeout

        self._connection_kwargs = connection_kwargs
        self._connection = None
        self._producer = None

        # TODO: remove useless middleware filter
        if not is_test_env():
            self._middlewares = (
                CriticalLogMiddleware(self.logger, log_level),
                *self._middlewares,
            )

        # FastDepends args
        self._is_apply_types = apply_types
        self._is_validate = validate
        self._get_dependant = _get_dependant
        self._call_decorators = _call_decorators

        # AsyncAPI information
        self.url = specification_url
        self.protocol = protocol
        self.protocol_version = protocol_version
        self.description = description
        self.tags = tags
        self.security = security

    async def __aenter__(self) -> "Self":
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional["TracebackType"],
    ) -> None:
        await self.close(exc_type, exc_val, exc_tb)

    @abstractmethod
    async def start(self) -> None:
        """Start the broker async use case."""
        self._abc_start()
        await self.connect()

    async def connect(self, **kwargs: Any) -> ConnectionType:
        """Connect to a remote server."""
        if self._connection is None:
            connection_kwargs = self._connection_kwargs.copy()
            connection_kwargs.update(kwargs)
            self._connection = await self._connect(**connection_kwargs)
        self._setup()
        return self._connection

    @abstractmethod
    async def _connect(self) -> ConnectionType:
        """Connect to a resource."""
        raise NotImplementedError()

    def _setup(self) -> None:
        """Prepare all Broker entities to startup."""
        for h in self._subscribers.values():
            self.setup_subscriber(h)

        for p in self._publishers.values():
            self.setup_publisher(p)

    def setup_subscriber(
        self,
        subscriber: SubscriberProto[MsgType],
        **kwargs: Any,
    ) -> None:
        """Setup the Subscriber to prepare it to starting."""
        data = self._subscriber_setup_extra.copy()
        data.update(kwargs)
        subscriber._setup(**data)

    def setup_publisher(
        self,
        publisher: "PublisherProto[MsgType]",
        **kwargs: Any,
    ) -> None:
        """Setup the Publisher to prepare it to starting."""
        data = self._publisher_setup_extra.copy()
        data.update(kwargs)
        publisher._setup(**data)

    @property
    def _subscriber_setup_extra(self) -> "AnyDict":
        return {
            "logger": self.logger,
            "producer": self._producer,
            "graceful_timeout": self.graceful_timeout,
            "extra_context": {
                "broker": self,
                "logger": self.logger,
            },
            # broker options
            "broker_parser": self._parser,
            "broker_decoder": self._decoder,
            # dependant args
            "apply_types": self._is_apply_types,
            "is_validate": self._is_validate,
            "_get_dependant": self._get_dependant,
            "_call_decorators": self._call_decorators,
        }

    @property
    def _publisher_setup_extra(self) -> "AnyDict":
        return {
            "producer": self._producer,
        }

    def publisher(self, *args: Any, **kwargs: Any) -> "PublisherProto[MsgType]":
        pub = super().publisher(*args, **kwargs)
        if self.running:
            self.setup_publisher(pub)
        return pub

    def _abc_start(self) -> None:
        for h in self._subscribers.values():
            log_context = h.get_log_context(None)
            log_context.pop("message_id", None)
            self._setup_log_context(**log_context)

        if not self.running:
            self.running = True

            if not self.use_custom and self.logger is not None:
                set_logger_fmt(
                    cast(logging.Logger, self.logger),
                    self._get_fmt(),
                )

    async def close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        """Closes the object."""
        self.running = False

        for h in self._subscribers.values():
            await h.close()

        if self._connection is not None:
            await self._close(exc_type, exc_val, exc_tb)

    @abstractmethod
    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        """Close the object."""
        self._connection = None

    async def publish(
        self,
        msg: Any,
        *,
        producer: Optional["ProducerProto"],
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[Any]:
        """Publish message directly."""
        assert producer, NOT_CONNECTED_YET  # nosec B101

        publish = producer.publish

        for m in self._middlewares:
            publish = partial(m(None).publish_scope, publish)

        return await publish(msg, correlation_id=correlation_id, **kwargs)

    async def request(
        self,
        msg: Any,
        *,
        producer: Optional["ProducerProto"],
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Publish message directly."""
        assert producer, NOT_CONNECTED_YET  # nosec B101

        request = producer.request
        for m in self._middlewares:
            request = partial(m(None).publish_scope, request)

        published_msg = await request(
            msg,
            correlation_id=correlation_id,
            **kwargs,
        )

        message: Any = await process_msg(
            msg=published_msg,
            middlewares=self._middlewares,
            parser=producer._parser,
            decoder=producer._decoder,
        )
        return message

    @abstractmethod
    async def ping(self, timeout: Optional[float]) -> bool:
        """Check connection alive."""
        raise NotImplementedError()
