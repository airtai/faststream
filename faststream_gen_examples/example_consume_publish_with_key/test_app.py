import pytest

from faststream import Context
from faststream.kafka import TestKafkaBroker

from .app import Point, broker, on_input_data


@broker.subscriber("output_data")
async def on_output_data(msg: Point, key: bytes = Context("message.raw_message.key")):
    pass


@pytest.mark.asyncio
async def test_point_was_incremented():
    async with TestKafkaBroker(broker):
        await broker.publish(Point(x=1.0, y=2.0), "input_data", key=b"key")
        on_input_data.mock.assert_called_with(dict(Point(x=1.0, y=2.0)))
        on_output_data.mock.assert_called_with(dict(Point(x=2.0, y=3.0)))
