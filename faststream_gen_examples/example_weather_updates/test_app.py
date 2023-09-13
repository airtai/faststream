import pytest

from faststream.kafka import TestKafkaBroker

from .app import WeatherConditions, broker, on_weather_updates


@broker.subscriber("weather_alerts")
async def on_weather_alerts(msg: WeatherConditions) -> None:
    pass


@pytest.mark.asyncio
async def test_not_published_to_weather_alerts():
    async with TestKafkaBroker(broker):
        await broker.publish(
            WeatherConditions(city="Zagreb", temperature=20.5, conditions="Sunny"),
            "weather_updates",
        )
        on_weather_updates.mock.assert_called_with(
            dict(WeatherConditions(city="Zagreb", temperature=20.5, conditions="Sunny"))
        )

        on_weather_alerts.mock.assert_not_called()


@pytest.mark.asyncio
async def test_published_to_weather_alerts():
    async with TestKafkaBroker(broker):
        await broker.publish(
            WeatherConditions(city="Zagreb", temperature=-15, conditions="Sunny"),
            "weather_updates",
        )
        on_weather_updates.mock.assert_called_with(
            dict(WeatherConditions(city="Zagreb", temperature=-15, conditions="Sunny"))
        )

        on_weather_alerts.mock.assert_called_with(
            dict(
                WeatherConditions(
                    city="Alert: Zagreb", temperature=-15, conditions="Sunny"
                )
            )
        )
