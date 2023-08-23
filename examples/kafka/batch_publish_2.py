from propan import Logger, PropanApp
from propan.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = PropanApp(broker)


@broker.subscriber("test", batch=True)
async def handle(msg: list[str], logger: Logger):
    logger.info(msg)


publisher = broker.publisher("test", batch=True)


@app.after_startup
async def test() -> None:
    await publisher.publish("hi", "propan")
