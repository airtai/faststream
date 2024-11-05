from faststream import FastStream, AckPolicy
from faststream.annotations import Logger
from faststream.rabbit import RabbitBroker

broker = RabbitBroker()
app = FastStream(broker)


@broker.subscriber("test-queue")
async def handle(msg, logger: Logger):
    logger.info(msg)
    return "Response"


@app.after_startup
async def test_publishing():
    await broker.publish("Hello!", "test-queue")
