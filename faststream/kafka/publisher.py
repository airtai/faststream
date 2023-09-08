from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence

from aiokafka import ConsumerRecord

from faststream.__about__ import __version__
from faststream._compat import override
from faststream.kafka.producer import AioKafkaFastProducer
from faststream.kafka.shared.publisher import ABCPublisher
from faststream.types import SendableMessage


@dataclass
class LogicPublisher(ABCPublisher[ConsumerRecord]):
    _producer: Optional[AioKafkaFastProducer] = field(default=None, init=False)
    batch: bool = field(default=False)
    client_id: str = field(default="faststream-" + __version__)

    @override
    async def publish(  # type: ignore[override]
        self,
        *messages: SendableMessage,
        message: SendableMessage = "",
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        assert self._producer, "Please, setup `_producer` first"  # nosec B101
        assert (  # nosec B101
            self.batch or len(messages) < 2
        ), "You can't send multiple messages without `batch` flag"

        if not self.batch:
            return await self._producer.publish(
                message=next(iter(messages), message),
                topic=self.topic,
                key=key or self.key,
                partition=partition or self.partition,
                timestamp_ms=timestamp_ms or self.timestamp_ms,
                correlation_id=correlation_id,
                headers=headers or self.headers,
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
                partition=partition or self.partition,
                timestamp_ms=timestamp_ms or self.timestamp_ms,
                headers=headers or self.headers,
            )
            return None
