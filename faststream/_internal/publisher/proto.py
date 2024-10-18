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
    from faststream.response.response import PublishCommand


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
    ) -> Optional[Any]:
        """Public method to publish a message.

        Should be called by user only `broker.publisher(...).publish(...)`.
        """
        ...

    @abstractmethod
    async def _publish(
        self,
        cmd: "PublishCommand",
        *,
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> Optional[Any]:
        """Private method to publish a message.

        Should be called inside `publish` method or as a step of `consume` scope.
        """
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
