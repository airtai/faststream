from propan import PropanApp
from propan.rabbit import RabbitBroker
from propan.rabbit.annotations import Logger, RabbitMessage

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = PropanApp(broker)


@broker.subscriber("test-queue")
async def handle(
    body,
    logger: Logger,
    message: RabbitMessage,
):
    await message.ack()  # ack first
    logger.info(body)


@app.after_startup
async def test_publishing():
    await broker.publish("Hello!", "test-queue")
