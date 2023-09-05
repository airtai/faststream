from typing import List

import pytest

from docs_src.kafka.publish_batch.app import (
    Data,
    broker,
    decrease_and_increase,
    on_input_data_1,
    on_input_data_2,
)
from faststream.kafka import TestKafkaBroker


# TODO: remove after https://github.com/airtai/fastkafka/pull/533 merged
@broker.subscriber("output_data", batch=True)
async def on_decrease_and_increase(msg: List[Data]):
    pass


@pytest.mark.asyncio
async def test_batch_publish_decorator():
    async with TestKafkaBroker(broker):
        await broker.publish(Data(data=2.0), "input_data_1")

        on_input_data_1.mock.assert_called_once_with(dict(Data(data=2.0)))
        decrease_and_increase.mock.assert_called_once_with(
            [dict(Data(data=1.0)), dict(Data(data=4.0))]
        )

        on_decrease_and_increase.mock.assert_called_once_with(
            [dict(Data(data=1.0)), dict(Data(data=4.0))]
        )


@pytest.mark.asyncio
async def test_batch_publish_call():
    async with TestKafkaBroker(broker):
        await broker.publish(Data(data=2.0), "input_data_2")

        on_input_data_2.mock.assert_called_once_with(dict(Data(data=2.0)))
        decrease_and_increase.mock.assert_called_once_with(
            [dict(Data(data=1.0)), dict(Data(data=4.0))]
        )

        on_decrease_and_increase.mock.assert_called_once_with(
            [dict(Data(data=1.0)), dict(Data(data=4.0))]
        )
