from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Optional,
    Protocol,
    Sequence,
)

from typing_extensions import override

from faststream.asyncapi.proto import AsyncAPIProto
from faststream.broker.proto import EndpointProto
from faststream.broker.types import MsgType

if TYPE_CHECKING:
    from faststream.broker.types import (
        AsyncCallable,
        BrokerMiddleware,
        P_HandlerParams,
        PublisherMiddleware,
        T_HandlerReturn,
    )
    from faststream.types import SendableMessage


class ProducerProto(Protocol):
    _parser: "AsyncCallable"
    _decoder: "AsyncCallable"

    @abstractmethod
    async def publish(
        self,
        message: "SendableMessage",
        /,
        *,
        correlation_id: Optional[str] = None,
    ) -> Optional[Any]:
        """Publishes a message asynchronously."""
        ...

    @abstractmethod
    async def request(
        self,
        message: "SendableMessage",
        /,
        *,
        correlation_id: Optional[str] = None,
    ) -> Any:
        """Publishes a message synchronously."""
        ...


class BasePublisherProto(Protocol):
    @abstractmethod
    async def publish(
        self,
        message: "SendableMessage",
        /,
        *,
        correlation_id: Optional[str] = None,
        _extra_middlewares: Sequence["PublisherMiddleware"] = (),
    ) -> Optional[Any]:
        """Publishes a message asynchronously."""
        ...

    @abstractmethod
    async def request(
        self,
        message: "SendableMessage",
        /,
        *,
        correlation_id: Optional[str] = None,
        _extra_middlewares: Sequence["PublisherMiddleware"] = (),
    ) -> Optional[Any]:
        """Publishes a message synchronously."""
        ...


class PublisherProto(
    AsyncAPIProto,
    EndpointProto,
    BasePublisherProto,
    Generic[MsgType],
):
    schema_: Any

    _broker_middlewares: Sequence["BrokerMiddleware[MsgType]"]
    _middlewares: Sequence["PublisherMiddleware"]
    _producer: Optional["ProducerProto"]

    @abstractmethod
    def add_middleware(self, middleware: "BrokerMiddleware[MsgType]") -> None: ...

    @staticmethod
    @abstractmethod
    def create() -> "PublisherProto[MsgType]":
        """Abstract factory to create a real Publisher."""
        ...

    @override
    @abstractmethod
    def setup(  # type: ignore[override]
        self,
        *,
        producer: Optional["ProducerProto"],
    ) -> None: ...

    @abstractmethod
    def __call__(
        self,
        func: "Callable[P_HandlerParams, T_HandlerReturn]",
    ) -> "Callable[P_HandlerParams, T_HandlerReturn]": ...
