from faststream import FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitQueue, QueueType

broker = RabbitBroker(max_consumers=10)
app = FastStream(broker)

queue = RabbitQueue(
    name="test-stream",
    durable=True,
    queue_type=QueueType.STREAM
)


@broker.subscriber(
    queue,
    consume_args={"x-stream-offset": "first"},
)
async def handle(msg, logger: Logger):
    logger.info("%s", msg)


@app.after_startup
async def test():
    await broker.publish("Hi!", queue)
