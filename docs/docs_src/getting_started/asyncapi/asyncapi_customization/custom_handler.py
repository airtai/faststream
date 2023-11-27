from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream
from faststream.kafka import KafkaBroker, KafkaMessage


class DataBasic(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher(
    "output_data",
    description="My publisher description",
    title="output_data:Produce",
    schema=DataBasic,
)
@broker.subscriber(
    "input_data", description="My subscriber description", title="input_data:Consume"
)
async def on_input_data(msg):
    # your processing logic
    pass
