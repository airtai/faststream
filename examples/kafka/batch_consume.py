from propan import Logger, PropanApp
from propan.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = PropanApp(broker)


@broker.subscriber("test", batch=True)
async def handle(msg: list[str], logger: Logger):
    logger.info(msg)


@app.after_startup
async def test() -> None:
    await broker.publish("hi", "test")
    await broker.publish("propan", "test")
