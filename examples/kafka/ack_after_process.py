from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker()
app = FastStream(broker)


@broker.subscriber(
    "test",
    group_id="group",
    auto_commit=False,
)
async def handler(msg: str, logger: Logger):
    logger.info(msg)


@app.after_startup
async def test():
    await broker.publish("Hi!", "test")
