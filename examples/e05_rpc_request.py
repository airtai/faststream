from faststream import FastStream
from faststream.annotations import Logger
from faststream.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)


@broker.subscriber("test-queue")
async def handle(msg, logger: Logger):
    logger.info(msg)
    return "pong"


@app.after_startup
async def test_publishing():
    assert (await broker.publish("ping", "test-queue", rpc=True)) == "pong"
