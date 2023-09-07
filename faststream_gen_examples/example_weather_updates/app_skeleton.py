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
    """
    Processes a message from the 'weather_updates' topic.
    Upon reception, the function should verify if the temperature attribute is above 40 or below -10.
    If yes, append the string 'Alert: ' to the city attribute and publish this message to 'weather_alerts' topic.

    Instructions:
    1. Consume a message from 'weather_updates' topic.
    2. Create a new message object (do not directly modify the original).
    3. Check if the temperature attribute is above 40 or below -10.
    4. If 3. is True, append the string 'Alert: ' to the city attribute and publish this message to 'weather_alerts' topic.

    """
    raise NotImplementedError()
