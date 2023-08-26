from typing import Any

import aiokafka

from faststream.broker.message import StreamMessage


class KafkaMessage(StreamMessage[aiokafka.ConsumerRecord]):
    async def ack(self, **kwargs: Any) -> None:
        return None

    async def nack(self, **kwargs: Any) -> None:
        return None

    async def reject(self, **kwargs: Any) -> None:
        return None
