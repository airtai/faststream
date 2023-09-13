import pytest

from faststream import Context, TestApp
from faststream.kafka import TestKafkaBroker

from .app import Weather, app, broker


@broker.subscriber("weather")
async def on_weather(msg: Weather, key: bytes = Context("message.raw_message.key")):
    pass


@pytest.mark.asyncio
async def test_message_was_published():
    async with TestKafkaBroker(broker):
        async with TestApp(app):
            await on_weather.wait_call(3)
            on_weather.mock.assert_called()
