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
    """
    Set all necessary global variables inside ContextRepo object:
        Set message_history for storing all input messages
    """
    raise NotImplementedError()


@broker.subscriber("weather")
async def on_weather(
    msg: Weather,
    logger: Logger,
    context: ContextRepo,
    key: bytes = Context("message.raw_message.key"),
) -> None:
    """
    Processes a message from the 'weather' topic. This topic uses partition key.
    Calculate the temperature mean of the last 5 messages for the given partition key
    Publish the temperature price mean to the temperature_mean topic and use the same partition key which the weather topic is using.

    Instructions:
    1. Consume a message from 'weather' topic.
    2. Save each message to a dictionary (global variable) - partition key should be usded as a dictionary key and value should be a List of temperatures.
    3. Calculate the temperature mean of the last 5 messages for the given partition key
    4. Publish the temperature price mean to the temperature_mean topic and use the same partition key which the weather topic is using.
    """
    raise NotImplementedError()
