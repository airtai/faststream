from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("intermediate_data")
@broker.subscriber("input_data")
async def on_input_data(msg: Data, logger: Logger) -> Data:
    return Data(data=msg.data+1.0)

@broker.publisher("output_data")
@broker.subscriber("intermediate_data")
async def on_intermediate(msg: Data, logger: Logger) -> Data:
    return Data(data=msg.data*2.0)

@broker.subscriber("output_data")
async def on_output_data(msg: Data):
    pass
