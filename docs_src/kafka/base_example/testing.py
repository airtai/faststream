import pytest

from docs_src.kafka.base_example.app import Data, broker, on_input_data
from faststream.kafka import TestKafkaBroker
from .app import (
    broker, 
    on_input_data, 
    Data
)

@pytest.mark.asyncio
async def test_base_app():
    @broker.subscriber("output_data")
    async def on_output_data(msg: Data):
        pass

    async with TestKafkaBroker(broker) as tester:
        await tester.publish(Data(data=0.2), "input_data")

        on_input_data.mock.assert_called_with(dict(Data(data=0.2)))

        on_output_data.mock.assert_called_once_with(dict(Data(data=1.2)))
