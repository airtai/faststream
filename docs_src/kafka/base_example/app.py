import asyncio
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

@broker.publisher("output_data")
@broker.subscriber("input_data")
async def on_input_data(data: float, logger: Logger) -> Data:
    logger.info(data)
    await asyncio.sleep(3)
    return Data(data=data+1.0)


# @broker.publisher("output_data")
# async def to_output_data(data: float) -> Data:
#     processed_data = Data(data=data+1.0)
#     return processed_data