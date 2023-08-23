from propan import PropanApp
from propan.annotations import Logger
from propan.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = PropanApp(broker)

publisher = broker.publisher("response-queue")


@broker.subscriber("test-queue")
async def handle(msg, logger: Logger):
    await publisher.publish("Response")
    logger.info(msg)


@broker.subscriber("response-queue")
async def handle_response(msg, logger: Logger):
    logger.info(f"Process response: {msg}")


@app.after_startup
async def test_publishing():
    await broker.publish("Hello!", "test-queue")
