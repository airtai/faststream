import pytest

from faststream.kafka import TestKafkaBroker
from docs_src.kafka.base_example.app import broker, on_input_data, Data

@pytest.mark.asyncio
async def test_base_app():
    @broker.subscriber("output_data")
    async def on_output_data(msg: Data):
        pass

    async with TestKafkaBroker(broker) as tester:

        await tester.publish(0.2, "input_data")

        # check an incoming message body
        # on_input_data.mock.assert_called_with({'data': 0.2})
        # on_input_data.mock.assert_called_with(dict(Data(data=0.2)))
        on_input_data.mock.assert_called_with(0.2)

        # check the publisher call
        # publisher.mock.assert_called_once_with(dict(Data(data=1.2)))

        # how to check for the incoming msg on the tester????
        on_output_data.mock.assert_called_once_with({"data": 1.2})