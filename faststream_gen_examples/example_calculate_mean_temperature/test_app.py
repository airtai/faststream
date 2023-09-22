from datetime import datetime

import pytest
from freezegun import freeze_time

from faststream import Context, TestApp
from faststream._compat import model_to_jsonable
from faststream.kafka import TestKafkaBroker

from .app import Weather, app, broker, on_weather


@broker.subscriber("temperature_mean")
async def on_temperature_mean(
    msg: float, key: bytes = Context("message.raw_message.key")
):
    pass


# Feeze time so the datetime always uses the same time
@freeze_time("2023-01-01")
@pytest.mark.asyncio
async def test_point_was_incremented():
    async with TestKafkaBroker(broker):
        async with TestApp(app):
            timestamp = datetime.now()
            await broker.publish(
                Weather(temperature=20.5, windspeed=20, timestamp=timestamp),
                "weather",
                key=b"ZG",
            )
            weather_json = model_to_jsonable(
                Weather(temperature=20.5, windspeed=20, timestamp=timestamp)
            )
            on_weather.mock.assert_called_with(weather_json)

            await broker.publish(
                Weather(temperature=10.5, windspeed=20, timestamp=timestamp),
                "weather",
                key=b"ZG",
            )
            weather_json = model_to_jsonable(
                Weather(temperature=10.5, windspeed=20, timestamp=timestamp)
            )
            on_weather.mock.assert_called_with(weather_json)

            on_temperature_mean.mock.assert_called_with(15.5)
