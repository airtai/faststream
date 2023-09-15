from statistics import mean
from typing import Dict, List

from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import Context, ContextRepo, FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


class Weather(BaseModel):
    temperature: float = Field(
        ..., examples=[20], description="Temperature in Celsius degrees"
    )
    windspeed: NonNegativeFloat = Field(
        ..., examples=[20], description="Wind speed in kilometers per hour"
    )


publisher = broker.publisher("temperature_mean")


@app.on_startup
async def app_setup(context: ContextRepo):
    message_history: Dict[str, List[float]] = {}
    context.set_global("message_history", message_history)


@broker.subscriber("weather")
async def on_weather(
    msg: Weather,
    logger: Logger,
    context: ContextRepo,
    key: bytes = Context("message.raw_message.key"),
) -> None:
    logger.info(f"Weather info {msg=}")

    message_history = context.get("message_history")

    weather_key = key.decode("utf-8")
    if weather_key not in message_history:
        message_history[weather_key] = []

    message_history[weather_key].append(msg.temperature)
    context.set_global("message_history", message_history)

    mean_temperature = mean(message_history[weather_key][-5:])
    await publisher.publish(mean_temperature, key=key)
