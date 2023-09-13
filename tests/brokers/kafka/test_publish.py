import asyncio

import pytest

from faststream.kafka import KafkaBroker
from tests.brokers.base.publish import BrokerPublishTestcase


@pytest.mark.kafka
class TestPublish(BrokerPublishTestcase):
    @pytest.mark.asyncio
    async def test_publish_batch(self, queue: str, broker: KafkaBroker):
        msgs_queue = asyncio.Queue(maxsize=2)

        @broker.subscriber(queue)
        async def handler(msg):
            await msgs_queue.put(msg)

        async with broker:
            await broker.start()

            await broker.publish_batch(1, "hi", topic=queue)

            result, _ = await asyncio.wait(
                (
                    asyncio.create_task(msgs_queue.get()),
                    asyncio.create_task(msgs_queue.get()),
                ),
                timeout=3,
            )

        assert {1, "hi"} == {r.result() for r in result}

    @pytest.mark.asyncio
    async def test_batch_publisher_manual(self, queue: str, broker: KafkaBroker):
        msgs_queue = asyncio.Queue(maxsize=2)

        @broker.subscriber(queue)
        async def handler(msg):
            await msgs_queue.put(msg)

        publisher = broker.publisher(queue, batch=True)

        async with broker:
            await broker.start()

            await publisher.publish(1, "hi")

            result, _ = await asyncio.wait(
                (
                    asyncio.create_task(msgs_queue.get()),
                    asyncio.create_task(msgs_queue.get()),
                ),
                timeout=3,
            )

        assert {1, "hi"} == {r.result() for r in result}

    @pytest.mark.asyncio
    async def test_batch_publisher_decorator(self, queue: str, broker: KafkaBroker):
        msgs_queue = asyncio.Queue(maxsize=2)

        @broker.subscriber(queue)
        async def handler(msg):
            await msgs_queue.put(msg)

        @broker.publisher(queue, batch=True)
        @broker.subscriber(queue + "1")
        async def pub(m):
            return 1, "hi"

        async with broker:
            await broker.start()

            await broker.publish("", queue + "1")

            result, _ = await asyncio.wait(
                (
                    asyncio.create_task(msgs_queue.get()),
                    asyncio.create_task(msgs_queue.get()),
                ),
                timeout=3,
            )

        assert {1, "hi"} == {r.result() for r in result}
