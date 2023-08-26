import asyncio

import pytest

from faststream.kafka import KafkaBroker
from tests.brokers.base.consume import BrokerRealConsumeTestcase


@pytest.mark.kafka
class TestConsume(BrokerRealConsumeTestcase):
    @pytest.mark.asyncio
    async def test_consume_batch(self, queue: str, broker: KafkaBroker):
        msgs_queue = asyncio.Queue(maxsize=1)

        @broker.subscriber(queue, batch=True)
        async def handler(msg):
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()

            await broker.publish_batch(1, "hi", topic=queue)

            result, _ = await asyncio.wait(
                (asyncio.create_task(msgs_queue.get()),),
                timeout=3,
            )

        assert [{1, "hi"}] == [set(r.result()) for r in result]
