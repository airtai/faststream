import pytest

from docs.docs_src.kafka.call_publish_within_subscribe.app import (
    Data,
    broker,
    on_input_data,
    to_decrement_data,
    to_increment_data,
)
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_base_app():
    @broker.subscriber("decrement_data")
    async def on_decrement_data(msg: Data):
        pass

    @broker.subscriber("increment_data")
    async def on_increment_data(msg: Data):
        pass

    async with TestKafkaBroker(broker):
        await broker.publish(Data(data=0.2), "input_data")

        on_input_data.mock.assert_called_with(dict(Data(data=0.2)))

        to_decrement_data.mock.assert_called_once_with(dict(Data(data=0.1)))
        to_increment_data.mock.assert_called_once_with(dict(Data(data=0.4)))

        on_decrement_data.mock.assert_called_once_with(dict(Data(data=0.1)))
        on_increment_data.mock.assert_called_once_with(dict(Data(data=0.4)))
