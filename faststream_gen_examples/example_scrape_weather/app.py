import asyncio
import json
from datetime import datetime

import requests
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import ContextRepo, FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


publisher = broker.publisher("weather")


class Weather(BaseModel):
    latitude: NonNegativeFloat = Field(
        ...,
        examples=[22.5],
        description="Latitude measures the distance north or south of the equator.",
    )
    longitude: NonNegativeFloat = Field(
        ...,
        examples=[55],
        description="Longitude measures distance east or west of the prime meridian.",
    )
    temperature: float = Field(
        ..., examples=[20], description="Temperature in Celsius degrees"
    )
    windspeed: NonNegativeFloat = Field(
        ..., examples=[20], description="Wind speed in kilometers per hour"
    )
    time: str = Field(
        ..., examples=["2023-09-13T07:00"], description="The time of the day"
    )


@app.on_startup
async def app_setup(context: ContextRepo):
    context.set_global("app_is_running", True)


@app.on_shutdown
async def shutdown(context: ContextRepo):
    context.set_global("app_is_running", False)

    # Get all the running tasks and wait them to finish
    publish_tasks = context.get("publish_tasks")
    await asyncio.wait(publish_tasks)


async def fetch_and_publish_weather(
    latitude: float,
    longitude: float,
    logger: Logger,
    context: ContextRepo,
    time_interval: int = 5,
) -> None:
    # Always use context: ContextRepo for storing app_is_running variable
    while context.get("app_is_running"):
        uri = f"https://api.open-meteo.com/v1/forecast?current_weather=true&latitude={latitude}&longitude={longitude}"
        response = requests.get(uri)

        if response.status_code == 200:
            # read json response
            raw_data = json.loads(response.content)
            temperature = raw_data["current_weather"]["temperature"]
            windspeed = raw_data["current_weather"]["windspeed"]
            time = raw_data["current_weather"]["time"]

            new_data = Weather(
                latitude=latitude,
                longitude=longitude,
                temperature=temperature,
                windspeed=windspeed,
                time=time,
            )
            key = str(latitude) + "_" + str(longitude)
            await publisher.publish(new_data, key=key.encode("utf-8"))
        else:
            logger.warning(f"Failed API request {uri} at time {datetime.now()}")
        await asyncio.sleep(time_interval)


@app.after_startup
async def publish_weather(logger: Logger, context: ContextRepo):
    logger.info("Starting publishing:")

    latitudes = [13, 50, 44, 24]
    longitudes = [17, 13, 45, 70]
    # start scraping and producing to kafka topic
    publish_tasks = [
        asyncio.create_task(
            fetch_and_publish_weather(latitude, longitude, logger, context)
        )
        for latitude, longitude in zip(latitudes, longitudes)
    ]
    # you need to save asyncio tasks so you can wait them to finish at app shutdown (the function with @app.on_shutdown function)
    context.set_global("publish_tasks", publish_tasks)
