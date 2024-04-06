from abc import abstractmethod
from typing import Any, Callable, Dict, Iterable, List, Optional

from fast_depends.dependencies import Depends
from typing_extensions import Self, override

from faststream.asyncapi.proto import AsyncAPIProto
from faststream.broker.message import StreamMessage
from faststream.broker.proto import EndpointProto
from faststream.broker.publisher.proto import BasePublisherProto, ProducerProto
from faststream.broker.subscriber.call_item import HandlerItem
from faststream.broker.types import (
    BrokerMiddleware,
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    SubscriberMiddleware,
)
from faststream.broker.wrapper.proto import WrapperProto
from faststream.types import AnyDict, LoggerProto


class SubscriberProto(
    AsyncAPIProto,
    EndpointProto,
    WrapperProto[MsgType],
):
    calls: List[HandlerItem[MsgType]]
    running: bool

    _broker_dependecies: Iterable[Depends]
    _broker_middlewares: Iterable[BrokerMiddleware[MsgType]]
    _producer: Optional[ProducerProto]

    @staticmethod
    @abstractmethod
    def create() -> "SubscriberProto[MsgType]":
        """Abstract factory to create a real Subscriber."""
        ...

    @abstractmethod
    def get_log_context(
        self,
        msg: Optional[StreamMessage[MsgType]],
        /,
    ) -> Dict[str, str]:
        ...

    @override
    @abstractmethod
    def setup(  # type: ignore[override]
        self,
        *,
        logger: Optional[LoggerProto],
        graceful_timeout: Optional[float],
        broker_parser: Optional[CustomParser[MsgType]],
        broker_decoder: Optional[CustomDecoder[StreamMessage[MsgType]]],
        producer: Optional[ProducerProto],
        extra_context: AnyDict,
        # FastDepends options
        apply_types: bool,
        is_validate: bool,
        _get_dependant: Optional[Callable[..., Any]],
    ) -> None:
        ...

    @abstractmethod
    def _make_response_publisher(
        self,
        message: StreamMessage[MsgType],
    ) -> Iterable[BasePublisherProto]:
        ...

    @property
    @abstractmethod
    def call_name(self) -> str:
        ...

    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    async def consume(self, msg: MsgType) -> Any:
        ...

    @abstractmethod
    def add_call(
        self,
        *,
        filter_: "Filter[StreamMessage[MsgType]]",
        parser_: "CustomParser[MsgType]",
        decoder_: "CustomDecoder[StreamMessage[MsgType]]",
        middlewares_: Iterable["SubscriberMiddleware"],
        dependencies_: Iterable["Depends"],
    ) -> Self:
        ...
