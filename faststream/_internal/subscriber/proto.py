from abc import abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import Self, override

from faststream._internal.proto import Endpoint
from faststream._internal.subscriber.call_wrapper.proto import WrapperProto
from faststream._internal.types import MsgType

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.publisher.proto import (
        BasePublisherProto,
        ProducerProto,
    )
    from faststream._internal.state import BrokerState, Pointer
    from faststream._internal.types import (
        BrokerMiddleware,
        CustomCallable,
        Filter,
        SubscriberMiddleware,
    )
    from faststream.message import StreamMessage
    from faststream.response import Response

    from .call_item import HandlerItem


class SubscriberProto(
    Endpoint,
    WrapperProto[MsgType],
):
    calls: list["HandlerItem[MsgType]"]
    running: bool

    _broker_dependencies: Iterable["Dependant"]
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
        extra_context: "AnyDict",
        # broker options
        broker_parser: Optional["CustomCallable"],
        broker_decoder: Optional["CustomCallable"],
        # dependant args
        state: "Pointer[BrokerState]",
    ) -> None: ...

    @abstractmethod
    def _make_response_publisher(
        self,
        message: "StreamMessage[MsgType]",
    ) -> Iterable["BasePublisherProto"]: ...

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
        dependencies_: Iterable["Dependant"],
    ) -> Self: ...
