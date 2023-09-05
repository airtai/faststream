import pytest

from faststream.kafka import TestKafkaBroker

from .app import Data, broker, on_input_data, decrease_and_increase


@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish(Data(data=1.2), "input_data")

        on_input_data.mock.assert_called_once_with(dict(Data(data=1.2)))
        decrease_and_increase.mock.assert_called_once_with([dict(Data(data=0.2)), dict(Data(data=2.2))])
