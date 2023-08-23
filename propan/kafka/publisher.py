from dataclasses import dataclass, field
from typing import Optional, Sequence

from aiokafka import ConsumerRecord

from propan.__about__ import __version__
from propan._compat import override
from propan.kafka.producer import AioKafkaPropanProducer
from propan.kafka.shared.publisher import ABCPublisher
from propan.types import SendableMessage


@dataclass
class LogicPublisher(ABCPublisher[ConsumerRecord]):
    _producer: Optional[AioKafkaPropanProducer] = field(default=None, init=False)
    batch: bool = field(default=False)
    client_id: str = field(default="propan-" + __version__)

    @override
    async def publish(  # type: ignore[override]
        self,
        *messages: SendableMessage,
        message: SendableMessage = "",
        correlation_id: str = "",
    ) -> Optional[SendableMessage]:
        assert self._producer, "Please, setup `_producer` first"
        assert (
            self.batch or len(messages) < 2
        ), "You can't send multiple messages without `batch` flag"

        if not self.batch:
            return await self._producer.publish(
                message=next(iter(messages), message),
                topic=self.topic,
                key=self.key,
                partition=self.partition,
                timestamp_ms=self.timestamp_ms,
                headers={
                    "correlation_id": correlation_id,
                    **(self.headers or {}),
                },
                reply_to=self.reply_to or "",
            )
        else:
            to_send: Sequence[SendableMessage]
            if not messages:
                if not isinstance(message, Sequence):
                    raise ValueError(
                        f"Message: {messages} should be Sequence type to send in batch"
                    )
                else:
                    to_send = message
            else:
                to_send = messages

            await self._producer.publish_batch(
                *to_send,
                topic=self.topic,
                partition=self.partition,
                timestamp_ms=self.timestamp_ms,
                headers=self.headers,
            )
            return None
