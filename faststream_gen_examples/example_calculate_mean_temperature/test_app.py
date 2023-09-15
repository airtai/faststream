import pytest

from faststream import Context, TestApp
from faststream.kafka import TestKafkaBroker

from .app import Weather, app, broker


@broker.subscriber("temperature_mean")
async def on_temperature_mean(
    msg: float, key: bytes = Context("message.raw_message.key")
):
    pass


@pytest.mark.asyncio
async def test_point_was_incremented():
    async with TestKafkaBroker(broker):
        async with TestApp(app):
            await broker.publish(
                Weather(temperature=20.5, windspeed=20), "weather", key=b"ZG"
            )
            await broker.publish(
                Weather(temperature=10.5, windspeed=20), "weather", key=b"ZG"
            )
            on_temperature_mean.mock.assert_called_with(15.5)
