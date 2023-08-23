from propan import PropanApp
from propan.annotations import Logger
from propan.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = PropanApp(broker)


@broker.subscriber("test-queue")
async def handle(msg, logger: Logger):
    logger.info(msg)


@app.after_startup
async def test_publishing():
    await broker.publish("Hello!", "test-queue")
