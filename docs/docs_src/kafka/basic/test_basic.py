import pytest

from faststream.kafka import TestKafkaBroker

from .basic import DataBasic, broker, on_input_data


@pytest.mark.asyncio
async def test_base_app():
    @broker.subscriber("output_data")
    async def on_output_data(msg: DataBasic):
        pass

    async with TestKafkaBroker(broker) as tester:
        await tester.publish(DataBasic(data=0.2), "input_data")

        on_input_data.mock.assert_called_with(dict(DataBasic(data=0.2)))

        on_output_data.mock.assert_called_once_with(dict(DataBasic(data=1.2)))
