import pytest

from faststream.kafka import TestKafkaBroker
from .app_chain import (
    Data,
    broker,
)

@pytest.mark.asyncio
async def test_end_to_end():
    
    @broker.subscriber("output_data")
    async def on_output_data(msg: Data):
        pass

    async with TestKafkaBroker(broker) as tester:
        await tester.publish(Data(data=0.2), "input_data")
        on_output_data.mock.assert_called_once_with({"data": 2.4})