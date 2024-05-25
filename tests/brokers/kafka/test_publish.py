import asyncio

import pytest

from faststream.kafka import KafkaBroker
from tests.brokers.base.publish import BrokerPublishTestcase


@pytest.mark.kafka()
class TestPublish(BrokerPublishTestcase):
    def get_broker(self, apply_types: bool = False):
        return KafkaBroker(apply_types=apply_types)

    @pytest.mark.asyncio()
    async def test_publish_batch(self, queue: str):
        pub_broker = self.get_broker()

        msgs_queue = asyncio.Queue(maxsize=2)

        @pub_broker.subscriber(queue)
        async def handler(msg):
            await msgs_queue.put(msg)

        async with self.patch_broker(pub_broker) as br:
            await br.start()

            await br.publish_batch(1, "hi", topic=queue)

            result, _ = await asyncio.wait(
                (
                    asyncio.create_task(msgs_queue.get()),
                    asyncio.create_task(msgs_queue.get()),
                ),
                timeout=3,
            )

        assert {1, "hi"} == {r.result() for r in result}

    @pytest.mark.asyncio()
    async def test_batch_publisher_manual(self, queue: str):
        pub_broker = self.get_broker()

        msgs_queue = asyncio.Queue(maxsize=2)

        @pub_broker.subscriber(queue)
        async def handler(msg):
            await msgs_queue.put(msg)

        publisher = pub_broker.publisher(queue, batch=True)

        async with self.patch_broker(pub_broker) as br:
            await br.start()

            await publisher.publish(1, "hi")

            result, _ = await asyncio.wait(
                (
                    asyncio.create_task(msgs_queue.get()),
                    asyncio.create_task(msgs_queue.get()),
                ),
                timeout=3,
            )

        assert {1, "hi"} == {r.result() for r in result}

    @pytest.mark.asyncio()
    async def test_batch_publisher_decorator(self, queue: str):
        pub_broker = self.get_broker()

        msgs_queue = asyncio.Queue(maxsize=2)

        @pub_broker.subscriber(queue)
        async def handler(msg):
            await msgs_queue.put(msg)

        @pub_broker.publisher(queue, batch=True)
        @pub_broker.subscriber(queue + "1")
        async def pub(m):
            return 1, "hi"

        async with self.patch_broker(pub_broker) as br:
            await br.start()

            await br.publish("", queue + "1")

            result, _ = await asyncio.wait(
                (
                    asyncio.create_task(msgs_queue.get()),
                    asyncio.create_task(msgs_queue.get()),
                ),
                timeout=3,
            )

        assert {1, "hi"} == {r.result() for r in result}
