from abc import abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Callable, Optional

from typing_extensions import Self, override

from faststream._internal.proto import Endpoint
from faststream._internal.subscriber.call_wrapper.proto import WrapperProto
from faststream._internal.types import MsgType
from faststream.specification.base.proto import EndpointProto

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream._internal.basic_types import AnyDict, Decorator, LoggerProto
    from faststream._internal.publisher.proto import (
        BasePublisherProto,
        ProducerProto,
    )
    from faststream._internal.subscriber.call_item import HandlerItem
    from faststream._internal.types import (
        BrokerMiddleware,
        CustomCallable,
        Filter,
        SubscriberMiddleware,
    )
    from faststream.message import StreamMessage
    from faststream.response import Response


class SubscriberProto(
    EndpointProto,
    Endpoint,
    WrapperProto[MsgType],
):
    calls: list["HandlerItem[MsgType]"]
    running: bool

    _broker_dependencies: Iterable["Depends"]
    _broker_middlewares: Iterable["BrokerMiddleware[MsgType]"]
    _producer: Optional["ProducerProto"]

    @abstractmethod
    def add_middleware(self, middleware: "BrokerMiddleware[MsgType]") -> None: ...

    @abstractmethod
    def get_log_context(
        self,
        msg: Optional["StreamMessage[MsgType]"],
        /,
    ) -> dict[str, str]: ...

    @override
    @abstractmethod
    def _setup(  # type: ignore[override]
        self,
        *,
        logger: Optional["LoggerProto"],
        graceful_timeout: Optional[float],
        broker_parser: Optional["CustomCallable"],
        broker_decoder: Optional["CustomCallable"],
        producer: Optional["ProducerProto"],
        extra_context: "AnyDict",
        # FastDepends options
        apply_types: bool,
        is_validate: bool,
        _get_dependant: Optional[Callable[..., Any]],
        _call_decorators: Iterable["Decorator"],
    ) -> None: ...

    @abstractmethod
    def _make_response_publisher(
        self,
        message: "StreamMessage[MsgType]",
    ) -> Iterable["BasePublisherProto"]: ...

    @property
    @abstractmethod
    def call_name(self) -> str: ...

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def consume(self, msg: MsgType) -> Any: ...

    @abstractmethod
    async def process_message(self, msg: MsgType) -> "Response": ...

    @abstractmethod
    async def get_one(
        self,
        *,
        timeout: float = 5.0,
    ) -> "Optional[StreamMessage[MsgType]]": ...

    @abstractmethod
    def add_call(
        self,
        *,
        filter_: "Filter[Any]",
        parser_: "CustomCallable",
        decoder_: "CustomCallable",
        middlewares_: Iterable["SubscriberMiddleware[Any]"],
        dependencies_: Iterable["Depends"],
    ) -> Self: ...
