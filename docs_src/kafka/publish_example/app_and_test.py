from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream
from faststream.kafka import KafkaBroker, TestKafkaBroker

class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

@broker.publisher("input_data")
async def to_input_data(msg: Data) -> Data:
    return Data(data=msg.data+5.0)

@broker.subscriber("input_data")
async def on_input_data(msg: Data):
    pass


import pytest

@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker) as tester_broker:

        # Why is this failing
        with pytest.raises(Exception) as e:
            # We need to be able to call publisher functions like this
            await to_input_data(Data(data=0.2))
            on_input_data.mock.assert_called_once_with(Data(data=5.2))
            
