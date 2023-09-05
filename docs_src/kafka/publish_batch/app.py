from pydantic import BaseModel, Field, NonNegativeFloat
from typing import List

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


decrease_and_increase = broker.publisher("output_data", batch=True)


@decrease_and_increase
@broker.subscriber("input_data")
async def on_input_data(msg: Data, logger: Logger) -> None:
    logger.info(msg)
    await decrease_and_increase.publish(Data(data=(msg.data * .5)), Data(data=(msg.data * 2.0)))

@broker.subscriber("output_data", batch=True)
async def to_output_data(msg: List[Data]):
    pass

# or this
# @decrease_and_increase
# @broker.subscriber("input_data")
# async def on_input_data(msg: Data) -> List[Data]:
#     return Data(data=(msg.data - 1.0)), Data(data=(msg.data + 1.0))

import pytest

from faststream.kafka import TestKafkaBroker

#from .app import Data, broker, on_input_data, to_output_data


@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish(Data(data=1.0), "input_data")

        on_input_data.mock.assert_called_once_with(dict(Data(data=1.0)))
        decrease_and_increase.mock.assert_called_once_with([dict(Data(data=.5)), dict(Data(data=2.0))])
