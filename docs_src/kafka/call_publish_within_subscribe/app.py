from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

@broker.subscriber("input_data")
async def on_input_data(msg: Data, logger: Logger):
    logger.info(f"Consuming: {msg}")
    await to_output_data(msg, logger)


@broker.publisher("output_data")
async def to_output_data(msg: Data, logger: Logger) -> Data:
    msg_new = Data(data=msg.data+1.0)
    logger.info(f"Publishing: {msg_new}")
    return msg_new