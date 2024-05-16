from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterable, Optional, Protocol

from typing_extensions import override

from faststream.asyncapi.proto import AsyncAPIProto
from faststream.broker.proto import EndpointProto
from faststream.broker.types import MsgType

if TYPE_CHECKING:
    from faststream.broker.types import (
        BrokerMiddleware,
        P_HandlerParams,
        PublisherMiddleware,
        T_HandlerReturn,
    )
    from faststream.types import SendableMessage


class ProducerProto(Protocol):
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


class BasePublisherProto(Protocol):
    @abstractmethod
    async def publish(
        self,
        message: "SendableMessage",
        /,
        *,
        correlation_id: Optional[str] = None,
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> Optional[Any]:
        """Publishes a message asynchronously."""
        ...


class PublisherProto(
    AsyncAPIProto,
    EndpointProto,
    BasePublisherProto,
    Generic[MsgType],
):
    schema_: Any

    _broker_middlewares: Iterable["BrokerMiddleware[MsgType]"]
    _middlewares: Iterable["PublisherMiddleware"]
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
