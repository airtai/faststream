import pytest

from faststream.rabbit import RabbitBroker, RabbitQueue


@pytest.mark.asyncio()
@pytest.mark.rabbit()
async def test_set_max():
    queue = RabbitQueue("test")

    broker = RabbitBroker(logger=None, max_consumers=10)

    @broker.subscriber(queue)
    async def handler(): ...

    async with broker:
        await broker.start()

        queue = await broker.declare_queue(queue)
        assert queue.channel._prefetch_count == 10
