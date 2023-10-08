import asyncio

import pytest

from faststream.nats import JStream, NatsBroker
from tests.brokers.base.consume import BrokerRealConsumeTestcase


@pytest.mark.nats
class TestConsume(BrokerRealConsumeTestcase):
    async def test_consume_js(
        self,
        queue: str,
        consume_broker: NatsBroker,
        stream: JStream,
        event: asyncio.Event,
    ):
        @consume_broker.subscriber(queue, stream=stream)
        def subscriber(m):
            event.set()

        await consume_broker.start()
        await asyncio.wait(
            (
                asyncio.create_task(
                    consume_broker.publish("hello", queue, stream=stream.name)
                ),
                asyncio.create_task(event.wait()),
            ),
            timeout=3,
        )

        assert event.is_set()
