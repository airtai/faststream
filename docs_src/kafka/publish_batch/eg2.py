from typing import List, Tuple
from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker()
batch_producer = broker.publisher("response", batch=True)

@broker.subscriber("test")
async def handle(msg: int) -> None:
    await batch_producer.publish(1, 2, 3)

@broker.subscriber("response", batch=True)
async def handle_response(msg: List[int], logger: Logger):
    logger.info(msg)

app = FastStream(broker)

# @app.after_startup
# async def test():
#     await broker.publish("", "test")


import pytest

from faststream.kafka import TestKafkaBroker



@pytest.mark.asyncio
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish(1, "test")

        # on_input_data.mock.assert_called_once_with(dict(Data(data=1.2)))
        # decrease_and_increase.mock.assert_called_once_with([dict(Data(data=0.2)), dict(Data(data=2.2))])
