from abc import abstractmethod
from collections.abc import Iterable, Sequence
from functools import partial
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Generic,
    Optional,
    Union,
    cast,
)

from typing_extensions import Doc, Self

from faststream._internal.context.repository import context
from faststream._internal.setup import (
    EmptyState,
    FastDependsData,
    LoggerState,
    SetupAble,
    SetupState,
)
from faststream._internal.setup.state import BaseState
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
from faststream.message.source_type import SourceType
from faststream.middlewares.logging import CriticalLogMiddleware

from .abc_broker import ABCBroker

if TYPE_CHECKING:
    from types import TracebackType

    from fast_depends.dependencies import Depends

    from faststream._internal.basic_types import AnyDict, Decorator
    from faststream._internal.publisher.proto import (
        ProducerProto,
        PublisherProto,
    )
    from faststream.response.response import PublishCommand
    from faststream.security import BaseSecurity
    from faststream.specification.schema.tag import Tag, TagDict


class BrokerUsecase(
    ABCBroker[MsgType],
    SetupAble,
    Generic[MsgType, ConnectionType],
):
    """A class representing a broker async use case."""

    url: Union[str, Sequence[str]]
    _connection: Optional[ConnectionType]
    _producer: Optional["ProducerProto"]
    _state: BaseState

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
                "Graceful shutdown timeout. Broker waits for all running subscribers completion before shut down.",
            ),
        ],
        # Logging args
        logger_state: LoggerState,
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
            Union[str, list[str]],
            Doc("AsyncAPI hardcoded server addresses."),
        ],
        security: Annotated[
            Optional["BaseSecurity"],
            Doc(
                "Security options to connect broker and generate AsyncAPI server security.",
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
        )

        self.running = False
        self.graceful_timeout = graceful_timeout

        self._connection_kwargs = connection_kwargs
        self._connection = None
        self._producer = None

        self._middlewares = (
            CriticalLogMiddleware(logger_state),
            *self._middlewares,
        )

        self._state = EmptyState(
            depends_params=FastDependsData(
                apply_types=apply_types,
                is_validate=validate,
                get_dependent=_get_dependant,
                call_decorators=_call_decorators,
            ),
            logger_state=logger_state,
        )

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
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional["TracebackType"],
    ) -> None:
        await self.close(exc_type, exc_val, exc_tb)

    @abstractmethod
    async def start(self) -> None:
        """Start the broker async use case."""
        # TODO: filter by already running handlers after TestClient refactor
        for handler in self._subscribers:
            self._state.logger_state.log(
                f"`{handler.call_name}` waiting for messages",
                extra=handler.get_log_context(None),
            )
            await handler.start()

    async def connect(self, **kwargs: Any) -> ConnectionType:
        """Connect to a remote server."""
        if self._connection is None:
            connection_kwargs = self._connection_kwargs.copy()
            connection_kwargs.update(kwargs)
            self._connection = await self._connect(**connection_kwargs)

        return self._connection

    @abstractmethod
    async def _connect(self) -> ConnectionType:
        """Connect to a resource."""
        raise NotImplementedError

    def _setup(self, state: Optional[BaseState] = None) -> None:
        """Prepare all Broker entities to startup."""
        if not self._state:
            # Fallback to default state if there no
            # parent container like FastStream object
            default_state = self._state.copy_to_state(SetupState)

            if state:
                self._state = state.copy_with_params(
                    depends_params=default_state.depends_params,
                    logger_state=default_state.logger_state,
                )
            else:
                self._state = default_state

        if not self.running:
            self.running = True

            for h in self._subscribers:
                log_context = h.get_log_context(None)
                log_context.pop("message_id", None)
                self._state.logger_state.params_storage.setup_log_contest(
                    log_context
                )

            self._state._setup()

        # TODO: why we can't move it to running?
        # TODO: can we setup subscriber in running broker automatically?
        for h in self._subscribers:
            self.setup_subscriber(h)

        for p in self._publishers:
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
            "logger": self._state.logger_state.logger.logger,
            "producer": self._producer,
            "graceful_timeout": self.graceful_timeout,
            "extra_context": {
                "broker": self,
                "logger": self._state.logger_state.logger.logger,
            },
            # broker options
            "broker_parser": self._parser,
            "broker_decoder": self._decoder,
            # dependant args
            "state": self._state,
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

    async def close(
        self,
        exc_type: Optional[type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        """Closes the object."""
        for h in self._subscribers:
            await h.close()

        self.running = False

    async def _basic_publish(
        self,
        cmd: "PublishCommand",
        *,
        producer: Optional["ProducerProto"],
    ) -> Optional[Any]:
        """Publish message directly."""
        assert producer, NOT_CONNECTED_YET  # nosec B101

        publish = producer.publish

        for m in self._middlewares:
            publish = partial(m(None, context=context).publish_scope, publish)

        return await publish(cmd)

    async def _basic_publish_batch(
        self,
        cmd: "PublishCommand",
        *,
        producer: Optional["ProducerProto"],
    ) -> None:
        """Publish a messages batch directly."""
        assert producer, NOT_CONNECTED_YET  # nosec B101

        publish = producer.publish_batch

        for m in self._middlewares:
            publish = partial(m(None, context=context).publish_scope, publish)

        await publish(cmd)

    async def _basic_request(
        self,
        cmd: "PublishCommand",
        *,
        producer: Optional["ProducerProto"],
    ) -> Any:
        """Publish message directly."""
        assert producer, NOT_CONNECTED_YET  # nosec B101

        request = producer.request
        for m in self._middlewares:
            request = partial(m(None, context=context).publish_scope, request)

        published_msg = await request(cmd)

        response_msg: Any = await process_msg(
            msg=published_msg,
            middlewares=self._middlewares,
            parser=producer._parser,
            decoder=producer._decoder,
            source_type=SourceType.Response,
        )
        return response_msg

    @abstractmethod
    async def ping(self, timeout: Optional[float]) -> bool:
        """Check connection alive."""
        raise NotImplementedError
