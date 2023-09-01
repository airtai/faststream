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
    # We need to be able to call publisher methods within the subscriber
    await to_output_data(msg, logger)


@broker.publisher("output_data")
async def to_output_data(msg: Data, logger: Logger) -> Data:
    msg_new = Data(data=msg.data+1.0)
    logger.info(f"Publishing: {msg_new}")
    return msg_new

import pytest
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_base_app():
    @broker.subscriber("output_data")
    async def on_output_data(msg: Data):
        pass

    async with TestKafkaBroker(broker) as tester:
        await tester.publish(Data(data=0.2), "input_data")

        on_input_data.mock.assert_called_with(dict(Data(data=0.2)))   

        # why is this failing?
        with pytest.raises(Exception) as e:    
            on_output_data.mock.assert_called_once_with(dict(Data(data=1.2)))