import asyncio
from datetime import datetime

from faststream import ContextRepo, FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

publisher = broker.publisher("current_time")


@app.on_startup
async def app_setup(context: ContextRepo):
    context.set_global("app_is_running", True)


@app.on_shutdown
async def app_shutdown(context: ContextRepo):
    context.set_global("app_is_running", False)

    # Get the running task and await for it to finish
    publish_task = context.get("publish_task")
    await publish_task


async def publish_time_task(
    logger: Logger, context: ContextRepo, time_interval: int = 5
):
    # Always use context: ContextRepo for storing app_is_running variable
    while context.get("app_is_running"):
        current_time = datetime.now()
        await publisher.publish(current_time.isoformat())
        logger.info(f"Current time published: {current_time}")
        await asyncio.sleep(time_interval)


@app.after_startup
async def publish_time(logger: Logger, context: ContextRepo):
    logger.info("Starting publishing:")

    publish_task = asyncio.create_task(publish_time_task(logger, context))

    # you need to save asyncio task so you can wait for it to finish at app shutdown (the function with @app.on_shutdown function)
    context.set_global("publish_task", publish_task)
