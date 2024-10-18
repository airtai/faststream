from abc import abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, Protocol

from typing_extensions import override

from faststream._internal.proto import Endpoint
from faststream._internal.types import MsgType
from faststream.specification.base.proto import EndpointProto

if TYPE_CHECKING:
    from faststream._internal.basic_types import SendableMessage
    from faststream._internal.types import (
        AsyncCallable,
        BrokerMiddleware,
        P_HandlerParams,
        PublisherMiddleware,
        T_HandlerReturn,
    )


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
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
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
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> Optional[Any]:
        """Publishes a message synchronously."""
        ...


class PublisherProto(
    EndpointProto,
    Endpoint,
    BasePublisherProto,
    Generic[MsgType],
):
    schema_: Any

    _broker_middlewares: Iterable["BrokerMiddleware[MsgType]"]
    _middlewares: Iterable["PublisherMiddleware"]
    _producer: Optional["ProducerProto"]

    @abstractmethod
    def add_middleware(self, middleware: "BrokerMiddleware[MsgType]") -> None: ...

    @override
    @abstractmethod
    def _setup(  # type: ignore[override]
        self,
        *,
        producer: Optional["ProducerProto"],
    ) -> None: ...

    @abstractmethod
    def __call__(
        self,
        func: "Callable[P_HandlerParams, T_HandlerReturn]",
    ) -> "Callable[P_HandlerParams, T_HandlerReturn]": ...
