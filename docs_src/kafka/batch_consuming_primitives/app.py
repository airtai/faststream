from typing import List

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test_batch", batch=True)
async def handle_batch(msg: List[str], logger: Logger):
    logger.info(msg)
