import pytest

from faststream.kafka import TestKafkaBroker

from .app import Data, broker, on_input_data, to_output_data


@pytest.mark.asyncio
async def test_base_app():
    @broker.subscriber("output_data")
    async def on_output_data(msg: Data):
        pass

    async with TestKafkaBroker(broker, with_real=True) as tester:
        await tester.publish(Data(data=0.2), "input_data")

        await on_input_data.wait_call(3)
        await on_output_data.wait_call(3)

        on_input_data.mock.assert_called_with(dict(Data(data=0.2)))
        to_output_data.mock.assert_called_with(dict(Data(data=1.2)))
        on_output_data.mock.assert_called_once_with(dict(Data(data=1.2)))
