import asyncio
from unittest.mock import patch

import pytest
from nats.aio.msg import Msg

from faststream.exceptions import AckMessage
from faststream.nats import JStream, NatsBroker, PullSub
from faststream.nats.annotations import NatsMessage
from tests.brokers.base.consume import BrokerRealConsumeTestcase
from tests.tools import spy_decorator


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

    async def test_consume_pull(
        self,
        queue: str,
        consume_broker: NatsBroker,
        stream: JStream,
        event: asyncio.Event,
        mock,
    ):
        @consume_broker.subscriber(queue, stream=stream, pull_sub=PullSub(1))
        def subscriber(m):
            mock(m)
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
        mock.assert_called_once_with("hello")

    @pytest.mark.asyncio
    async def test_consume_ack(
        self,
        queue: str,
        full_broker: NatsBroker,
        event: asyncio.Event,
        stream: JStream,
    ):
        @full_broker.subscriber(queue, stream=stream)
        async def handler(msg: NatsMessage):
            event.set()

        await full_broker.start()
        with patch.object(Msg, "ack", spy_decorator(Msg.ack)) as m:
            await asyncio.wait(
                (
                    asyncio.create_task(
                        full_broker.publish(
                            "hello",
                            queue,
                        )
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )
            m.mock.assert_called_once()

        assert event.is_set()

    @pytest.mark.asyncio
    async def test_consume_ack_manual(
        self,
        queue: str,
        full_broker: NatsBroker,
        event: asyncio.Event,
        stream: JStream,
    ):
        @full_broker.subscriber(queue, stream=stream)
        async def handler(msg: NatsMessage):
            await msg.ack()
            event.set()

        await full_broker.start()
        with patch.object(Msg, "ack", spy_decorator(Msg.ack)) as m:
            await asyncio.wait(
                (
                    asyncio.create_task(
                        full_broker.publish(
                            "hello",
                            queue,
                        )
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )
            m.mock.assert_called_once()

        assert event.is_set()

    @pytest.mark.asyncio
    async def test_consume_ack_raise(
        self,
        queue: str,
        full_broker: NatsBroker,
        event: asyncio.Event,
        stream: JStream,
    ):
        @full_broker.subscriber(queue, stream=stream)
        async def handler(msg: NatsMessage):
            event.set()
            raise AckMessage()

        await full_broker.start()
        with patch.object(Msg, "ack", spy_decorator(Msg.ack)) as m:
            await asyncio.wait(
                (
                    asyncio.create_task(
                        full_broker.publish(
                            "hello",
                            queue,
                        )
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )
            m.mock.assert_called_once()

        assert event.is_set()

    @pytest.mark.asyncio
    async def test_nack(
        self,
        queue: str,
        full_broker: NatsBroker,
        event: asyncio.Event,
        stream: JStream,
    ):
        @full_broker.subscriber(queue, stream=stream)
        async def handler(msg: NatsMessage):
            await msg.nack()
            event.set()

        await full_broker.start()
        with patch.object(Msg, "nak", spy_decorator(Msg.nak)) as m:
            await asyncio.wait(
                (
                    asyncio.create_task(
                        full_broker.publish(
                            "hello",
                            queue,
                        )
                    ),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )
            m.mock.assert_called_once()

        assert event.is_set()
