from faststream import FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitQueue

broker = RabbitBroker(max_consumers=10)
app = FastStream(broker)

queue = RabbitQueue(
    name="test",
    durable=True,
    arguments={
        "x-queue-type": "stream",
    },
)


@broker.subscriber(
    queue,
    consume_args={"x-stream-offset": "first"},
)
async def handle(msg, logger: Logger):
    logger.info(msg)


@app.after_startup
async def test():
    await broker.publish("Hi!", queue)
