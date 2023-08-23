from propan import PropanApp
from propan.annotations import Logger
from propan.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = PropanApp(broker)


@broker.subscriber("test-queue", filter=lambda m: m.content_type == "application/json")
async def handle_json(msg, logger: Logger):
    logger.info(f"JSON message: {msg}")


@broker.subscriber("test-queue")
async def handle_other_messages(msg, logger: Logger):
    logger.info(f"Default message: {msg}")


@app.after_startup
async def test_publishing():
    # send to `handle_json`
    await broker.publish({"msg": "Hello!"}, "test-queue")

    # send to `handle_other_messages`
    await broker.publish("Hello!", "test-queue")
