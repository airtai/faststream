import pytest

from faststream.kafka import TestKafkaBroker

from .app import Data, broker, on_input_data, to_output_data


@pytest.mark.asyncio
@pytest.mark.skip("not supported yet")
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish(Data(data=0.2), "input_data")

        on_input_data.mock.assert_called_once_with(dict(Data(data=0.2)))
        to_output_data.mock.assert_called_once_with(dict(Data(data=1.2)))
