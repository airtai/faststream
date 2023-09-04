from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker, TestKafkaBroker

class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("input_data")
async def on_input_data(msg: Data):
    pass


import pytest

@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish(Data(data=0.2), "input_data")
        on_input_data.mock.assert_called_once_with(dict(Data(data=0.2)))
            
