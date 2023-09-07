from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class WeatherConditions(BaseModel):
    city: str = Field(..., examples=["Zagreb"], description="City example")
    temperature: float
    conditions: str = Field(
        ..., examples=["Mostly Cloudy"], description="Conditions example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_weather_alerts = broker.publisher("weather_alerts")


@broker.subscriber("weather_updates")
async def on_weather_updates(msg: WeatherConditions, logger: Logger) -> None:
    logger.info(msg)

    if msg.temperature > 40 or msg.temperature < -10:
        alert_city = "Alert: " + msg.city
        alert_msg = WeatherConditions(
            city=alert_city, temperature=msg.temperature, conditions=msg.conditions
        )
        await to_weather_alerts.publish(alert_msg)
