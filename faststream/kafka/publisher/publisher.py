from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    Union,
    overload,
)

from typing_extensions import override

from faststream._internal.types import MsgType
from faststream.exceptions import SetupError
from faststream.kafka.publisher.usecase import (
    BatchPublisher,
    DefaultPublisher,
    LogicPublisher,
)
from faststream.specification.asyncapi.utils import resolve_payloads
from faststream.specification.schema.bindings import ChannelBinding, kafka
from faststream.specification.schema.channel import Channel
from faststream.specification.schema.message import CorrelationId, Message
from faststream.specification.schema.operation import Operation

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord

    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware


class SpecificationPublisher(LogicPublisher[MsgType]):
    """A class representing a publisher."""

    def get_name(self) -> str:
        return f"{self.topic}:Publisher"

    def get_schema(self) -> dict[str, Channel]:
        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,
                publish=Operation(
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads, "Publisher"),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id",
                        ),
                    ),
                ),
                bindings=ChannelBinding(kafka=kafka.ChannelBinding(topic=self.topic)),
            ),
        }

    @overload  # type: ignore[override]
    @staticmethod
    def create(
        *,
        batch: Literal[True],
        key: Optional[bytes],
        topic: str,
        partition: Optional[int],
        headers: Optional[dict[str, str]],
        reply_to: str,
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[tuple[ConsumerRecord, ...]]"],
        middlewares: Iterable["PublisherMiddleware"],
        # Specification args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> "SpecificationBatchPublisher": ...

    @overload
    @staticmethod
    def create(
        *,
        batch: Literal[False],
        key: Optional[bytes],
        topic: str,
        partition: Optional[int],
        headers: Optional[dict[str, str]],
        reply_to: str,
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[ConsumerRecord]"],
        middlewares: Iterable["PublisherMiddleware"],
        # Specification args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> "SpecificationDefaultPublisher": ...

    @overload
    @staticmethod
    def create(
        *,
        batch: bool,
        key: Optional[bytes],
        topic: str,
        partition: Optional[int],
        headers: Optional[dict[str, str]],
        reply_to: str,
        # Publisher args
        broker_middlewares: Iterable[
            "BrokerMiddleware[Union[tuple[ConsumerRecord, ...], ConsumerRecord]]"
        ],
        middlewares: Iterable["PublisherMiddleware"],
        # Specification args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> Union[
        "SpecificationBatchPublisher",
        "SpecificationDefaultPublisher",
    ]: ...

    @override
    @staticmethod
    def create(
        *,
        batch: bool,
        key: Optional[bytes],
        topic: str,
        partition: Optional[int],
        headers: Optional[dict[str, str]],
        reply_to: str,
        # Publisher args
        broker_middlewares: Iterable[
            "BrokerMiddleware[Union[tuple[ConsumerRecord, ...], ConsumerRecord]]"
        ],
        middlewares: Iterable["PublisherMiddleware"],
        # Specification args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> Union[
        "SpecificationBatchPublisher",
        "SpecificationDefaultPublisher",
    ]:
        if batch:
            if key:
                msg = "You can't setup `key` with batch publisher"
                raise SetupError(msg)

            return SpecificationBatchPublisher(
                topic=topic,
                partition=partition,
                headers=headers,
                reply_to=reply_to,
                broker_middlewares=broker_middlewares,
                middlewares=middlewares,
                schema_=schema_,
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )
        return SpecificationDefaultPublisher(
            key=key,
            # basic args
            topic=topic,
            partition=partition,
            headers=headers,
            reply_to=reply_to,
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )


class SpecificationBatchPublisher(
    BatchPublisher,
    SpecificationPublisher[tuple["ConsumerRecord", ...]],
):
    pass


class SpecificationDefaultPublisher(
    DefaultPublisher,
    SpecificationPublisher["ConsumerRecord"],
):
    pass
