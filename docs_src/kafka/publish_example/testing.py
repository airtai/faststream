import pytest

from faststream.kafka import TestKafkaBroker
from docs_src.kafka.publish_example.app import (
    broker, 
    on_input_data,
    to_input_data, 
    Data,
)

@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker) as tester:
        #await tester.publish(Data(data=0.2), "input_data")
        await to_input_data(Data(data=0.2))
        on_input_data.mock.assert_called_once_with(Data(data=5.2))
        
