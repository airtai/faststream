from typing import List, Tuple
from uuid import uuid4

from aiokafka import ConsumerRecord

from faststream.broker.message import StreamMessage
from faststream.broker.parsers import decode_message
from faststream.kafka.message import KafkaMessage
from faststream.types import DecodedMessage


class AioKafkaParser:
    @staticmethod
    async def parse_message(
        message: ConsumerRecord,
    ) -> StreamMessage[ConsumerRecord]:
        headers = {i: j.decode() for i, j in message.headers}
        return KafkaMessage(
            body=message.value,
            headers=headers,
            reply_to=headers.get("reply_to", ""),
            content_type=headers.get("content-type"),
            message_id=f"{message.offset}-{message.timestamp}",
            correlation_id=headers.get("correlation_id", str(uuid4())),
            raw_message=message,
        )

    @staticmethod
    async def parse_message_batch(
        message: Tuple[ConsumerRecord, ...],
    ) -> StreamMessage[Tuple[ConsumerRecord, ...]]:
        first = message[0]
        last = message[-1]
        headers = {i: j.decode() for i, j in first.headers}
        return KafkaMessage(
            body=[m.value for m in message],
            headers=headers,
            reply_to=headers.get("reply_to", ""),
            content_type=headers.get("content-type"),
            message_id=f"{first.offset}-{last.offset}-{first.timestamp}",
            correlation_id=headers.get("correlation_id", str(uuid4())),
            raw_message=message,
        )

    @staticmethod
    async def decode_message(msg: StreamMessage[ConsumerRecord]) -> DecodedMessage:
        return decode_message(msg)

    @classmethod
    async def decode_message_batch(
        cls, msg: StreamMessage[Tuple[ConsumerRecord, ...]]
    ) -> List[DecodedMessage]:
        return [decode_message(await cls.parse_message(m)) for m in msg.raw_message]
