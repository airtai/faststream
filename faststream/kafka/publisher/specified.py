from typing import TYPE_CHECKING

from faststream._internal.types import MsgType
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
