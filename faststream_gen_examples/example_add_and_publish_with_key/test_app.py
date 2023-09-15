import pytest

from faststream import Context, TestApp
from faststream.kafka import TestKafkaBroker

from .app import Point, app, broker


@broker.subscriber("output_data")
async def on_output_data(msg: Point, key: bytes = Context("message.raw_message.key")):
    pass


@pytest.mark.asyncio
async def test_point_was_incremented():
    async with TestKafkaBroker(broker):
        async with TestApp(app):
            await broker.publish(Point(x=1.0, y=2.0), "input_data", key=b"point_key")
            await broker.publish(Point(x=1.0, y=2.0), "input_data", key=b"point_key")

            on_output_data.mock.assert_called_with(dict(Point(x=2.0, y=4.0)))
