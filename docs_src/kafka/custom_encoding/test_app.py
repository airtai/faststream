from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker
from faststream.kafka.message import KafkaMessage

from aiokafka.structs import ConsumerRecord

from typing import Callable

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )

async def custom_parser(msg: ConsumerRecord, original: Callable[[ConsumerRecord], KafkaMessage]) -> KafkaMessage:
    kafka_msg = await original(msg)
    
    kafka_msg.body=Data.model_validate_json(kafka_msg.body.decode("utf-8"))

    return kafka_msg

@broker.subscriber("input_data", parser=custom_parser)
async def handle(msg: Data, logger: Logger) -> None:
    logger.info(f"handle({msg=})")

import pytest

from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_custom_parser():

    async with TestKafkaBroker(broker):

        msg = Data(data=0.5)

        # await broker.publish(msg, "input_data")
        await broker.publish(msg.model_dump_json().encode("utf-8"), "input_data")

        handle.mock.assert_called_once_with(Data(data=0.5))
        # handle.mock.assert_called_once_with(dict(Data(data=0.5)))

