from typing import Callable

from aiokafka.structs import ConsumerRecord
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker
from faststream.kafka.message import KafkaMessage

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


async def custom_parser(
    msg: ConsumerRecord, original: Callable[[ConsumerRecord], KafkaMessage]
) -> KafkaMessage:
    kafka_msg = await original(msg)

    if hasattr(Data, "model_validate_json"):
        kafka_msg.body = Data.model_validate_json(kafka_msg.body.decode("utf-8"))
    else:
        kafka_msg.body = Data.parse_raw(kafka_msg.body.decode("utf-8"))

    return kafka_msg


@broker.subscriber("input_data", parser=custom_parser)
async def handle(msg: Data, logger: Logger) -> None:
    logger.info(f"handle({msg=})")
