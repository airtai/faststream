from typing import List

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker()
batch_producer = broker.publisher("response", batch=True)


@batch_producer
@broker.subscriber("test")
async def handle():
    return 1, 2, 3


@broker.subscriber("response", batch=True)
async def handle_response(msg: List[int], logger: Logger):
    logger.info(msg)


app = FastStream(broker)


@app.after_startup
async def test():
    await broker.publish("", "test")
