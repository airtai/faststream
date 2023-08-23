from propan import PropanApp
from propan.annotations import Logger
from propan.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = PropanApp(broker)


@broker.subscriber("test-queue")
async def handle(msg, logger: Logger):
    logger.info(msg)
    return "pong"


@app.after_startup
async def test_publishing():
    assert "pong" == (await broker.publish("ping", "test-queue", rpc=True))
