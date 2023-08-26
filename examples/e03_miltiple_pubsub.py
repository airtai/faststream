from faststream import FastStream
from faststream.annotations import Logger
from faststream.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)


@broker.subscriber("test-queue")
@broker.publisher("response-queue")
@broker.subscriber("another-queue")
@broker.publisher("another-response-queue")
async def handle(msg, logger: Logger):
    logger.info(msg)
    return "Response"


@broker.subscriber("response-queue")
async def handle_response_1(msg, logger: Logger):
    logger.info(msg)


@broker.subscriber("another-response-queue")
async def handle_response_2(msg, logger: Logger):
    logger.info(msg)


@app.after_startup
async def test():
    await broker.publish("Hello!", "test-queue")
    await broker.publish("Hello!", "another-queue")
