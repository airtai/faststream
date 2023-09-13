from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import ContextRepo, FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


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
    """
    Set all necessary global variables inside ContextRepo object:
        Set app_is_running to True - we will use this variable as running loop condition
    """
    raise NotImplementedError()


@app.on_shutdown
async def shutdown(context: ContextRepo):
    """
    Set all necessary global variables inside ContextRepo object:
        Set app_is_running to False

    Get all executed tasks from context and wait them to finish
    """
    raise NotImplementedError()


async def fetch_and_publish_weather(
    latitude: float,
    longitude: float,
    logger: Logger,
    context: ContextRepo,
    time_inverval: int = 5,
) -> None:
    """
    While app_is_running variable inside context is True, repeat the following process:
        get the weather information by sending a GET request to "https://api.open-meteo.com/v1/forecast?current_weather=true"
        At the end of url you should add additional 'latitude' and 'longitude' parameters which are type float.
        Here is url example when you want to fetch information for latitude=52.3 and longitude=13.2:
            "https://api.open-meteo.com/v1/forecast?current_weather=true&latitude=52.3&longitude=13.2"

        from the response we want to get info about the temperature (float), windspeed (float) and time (string) and you can find them in:
            response["current_weather"]["temperature"], response["current_weather"]["windspeed"], and response["current_weather"]["time"]

        We need to fetch this data, construct the Weather object and publish it at 'weather' topic.
        For each message you are publishing we must use a key which will be constructed as:
            string value of latitude + '_' + string value of longitude

        asynchronous sleep for time_interval
    """
    raise NotImplementedError()


@app.after_startup
async def publish_weather(logger: Logger, context: ContextRepo):
    """
    Create asynchronous tasks for executing fetch_and_publish_weather function.
    Run this process for the following latitude and longitude combinations:
        - latitude=13 and longitude=17
        - latitude=50 and longitude=13
        - latitude=44 and longitude=45
        - latitude=24 and longitude=70
    Put all executed tasks to list and set it as global variable in context (It is needed so we can wait for this tasks at app shutdown)
    """
    raise NotImplementedError()
