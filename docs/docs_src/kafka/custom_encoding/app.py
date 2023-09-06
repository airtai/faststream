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


async def custom_decoder(msg: KafkaMessage) -> Data:
    if hasattr(Data, "model_validate_json"):
        return Data.model_validate_json(msg.body.decode("utf-8"))
    else:
        return Data.parse_raw(msg.body.decode("utf-8"))


@broker.subscriber("input_data", decoder=custom_decoder)
async def handle(msg: Data, logger: Logger) -> None:
    logger.info(f"handle({msg=})")
