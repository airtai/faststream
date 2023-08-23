from typing import Any

import aiokafka

from propan.broker.message import PropanMessage


class KafkaMessage(PropanMessage[aiokafka.ConsumerRecord]):
    async def ack(self, **kwargs: Any) -> None:
        return None

    async def nack(self, **kwargs: Any) -> None:
        return None

    async def reject(self, **kwargs: Any) -> None:
        return None
