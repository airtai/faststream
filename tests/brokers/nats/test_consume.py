import asyncio

import pytest

from faststream.nats import JStream, NatsBroker
from tests.brokers.base.consume import BrokerRealConsumeTestcase


@pytest.mark.nats
class TestConsume(BrokerRealConsumeTestcase):
    async def test_consume_js(
        self, queue: str, consume_broker: NatsBroker, stream: JStream
    ):
        @consume_broker.subscriber(queue, stream=stream)
        def subscriber(m):
            ...

        await consume_broker.start()
        await asyncio.wait(
            (
                asyncio.create_task(
                    consume_broker.publish("hello", queue, stream=stream.name)
                ),
                asyncio.create_task(subscriber.wait_call()),
            ),
            timeout=3,
        )

        assert subscriber.event.is_set()
