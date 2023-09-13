from faststream import ContextRepo, FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

publisher = broker.publisher("current_time")


@app.on_startup
async def app_setup(context: ContextRepo):
    """
    Set all necessary global variables inside ContextRepo object:
        Set app_is_running to True - we will use this variable as running loop condition
    """
    raise NotImplementedError()


@app.on_shutdown
async def app_shutdown(context: ContextRepo):
    """
    Set all necessary global variables inside ContextRepo object:
        Set app_is_running to False

    Get executed task from context and wait for it to finish
    """
    raise NotImplementedError()


async def publish_time_task(
    logger: Logger, context: ContextRepo, time_interval: int = 5
):
    """
    While app_is_running variable inside context is True, repeat the following process:
        publish the current time to the 'current_time' topic.
        asynchronous sleep for time_interval
    """
    raise NotImplementedError()


@app.after_startup
async def publish_time(logger: Logger, context: ContextRepo):
    """
    Create asynchronous task for executing publish_time_task function.
    Save asyncio task so you can wait for it to finish at app shutdown (the function with @app.on_shutdown function)
    """
    raise NotImplementedError()
