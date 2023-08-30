import pytest

from faststream.kafka import TestKafkaBroker
from docs_src.kafka.base_example.app import broker, on_input_data, to_output_data, Data

@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker) as tester:
        await tester.publish(Data(data=0.2), "input_data")

        # check an incoming message body
        on_input_data.mock.assert_called_with({'data': 0.2})

        # check the publisher call
        to_output_data.mock.assert_called_once_with(0.2)

        # how to check for the incoming msg on the tester????