from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, Iterable, Optional, Union, cast

from aiokafka import ConsumerRecord
from typing_extensions import override

from faststream.__about__ import __version__
from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.kafka.producer import AioKafkaFastProducer
from faststream.types import AnyDict, SendableMessage


@dataclass
class LogicPublisher(BasePublisher[ConsumerRecord]):
    """A class to publish messages to a Kafka topic.

    Attributes:
        _producer : An optional instance of AioKafkaFastProducer
        batch : A boolean indicating whether to send messages in batch
        client_id : A string representing the client ID

    Methods:
        publish : Publishes messages to the Kafka topic

    Raises:
        AssertionError: If `_producer` is not set up or if multiple messages are sent without the `batch` flag

    """

    topic: str = ""
    partition: Optional[int] = None
    timestamp_ms: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    reply_to: Optional[str] = ""
    client_id: str = field(default="faststream-" + __version__)

    _producer: Optional[AioKafkaFastProducer] = field(
        default=None,
        init=False,
        repr=False,
    )

    @cached_property
    def publish_kwargs(self) -> AnyDict:
        return {
            "topic": self.topic,
            "partition": self.partition,
            "timestamp_ms": self.timestamp_ms,
            "headers": self.headers,
            "reply_to": self.reply_to,
        }


@dataclass
class DefaultPublisher(LogicPublisher):
    key: Optional[bytes] = None

    @override
    async def _publish(  # type: ignore[override]
        self,
        message: SendableMessage = "",
        **kwargs: Any,
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101
        return await self._producer.publish(
            message=message,
            **kwargs,
        )

    @cached_property
    def publish_kwargs(self) -> AnyDict:
        return super().publish_kwargs | {"key": self.key}


class BatchPublisher(LogicPublisher):
    @override
    async def _publish(  # type: ignore[override]
        self,
        messages: Union[SendableMessage, Iterable[SendableMessage]],
        *extra_messages: SendableMessage,
        **kwargs: Any,
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        if extra_messages:
            msgs = (cast(SendableMessage, messages), *extra_messages)
        else:
            msgs = cast(Iterable[SendableMessage], messages)

        await self._producer.publish_batch(*msgs, **kwargs)
