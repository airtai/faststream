from typing import List

import pytest

from faststream.kafka import TestKafkaBroker

from .app import Data, broker, decrease_and_increase, on_input_data


@broker.subscriber("output_data", batch=True)
async def on_decrease_and_increase(msg: List[Data]):
    pass


@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish(Data(data=2.0), "input_data")

        on_input_data.mock.assert_called_once_with(dict(Data(data=2.0)))
        decrease_and_increase.mock.assert_called_once_with(
            [dict(Data(data=1.0)), dict(Data(data=4.0))]
        )

        on_decrease_and_increase.mock.assert_called_once_with(
            [dict(Data(data=1.0)), dict(Data(data=4.0))]
        )
