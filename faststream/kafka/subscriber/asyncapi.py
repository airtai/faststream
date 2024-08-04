from typing import (
    TYPE_CHECKING,
    Dict,
    Tuple,
)

from faststream.asyncapi.schema import (
    ChannelBinding,
    CorrelationId,
    Message,
    v2_6_0,
)
from faststream.asyncapi.schema.bindings import kafka
from faststream.asyncapi.utils import resolve_payloads
from faststream.broker.types import MsgType
from faststream.kafka.subscriber.usecase import (
    BatchSubscriber,
    DefaultSubscriber,
    LogicSubscriber,
)

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord


class AsyncAPISubscriber(LogicSubscriber[MsgType]):
    """A class to handle logic and async API operations."""

    def get_name(self) -> str:
        return f'{",".join(self.topics)}:{self.call_name}'

    def get_schema(self) -> Dict[str, v2_6_0.Channel]:
        channels = {}

        payloads = self.get_payloads()

        for t in self.topics:
            handler_name = self.title_ or f"{t}:{self.call_name}"

            channels[handler_name] = v2_6_0.Channel(
                description=self.description,
                subscribe=v2_6_0.Operation(
                    message=Message(
                        title=f"{handler_name}:Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    kafka=kafka.ChannelBinding(topic=t),
                ),
            )

        return channels


class AsyncAPIDefaultSubscriber(
    DefaultSubscriber,
    AsyncAPISubscriber["ConsumerRecord"],
):
    pass


class AsyncAPIBatchSubscriber(
    BatchSubscriber,
    AsyncAPISubscriber[Tuple["ConsumerRecord", ...]],
):
    pass
