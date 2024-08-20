import asyncio

import pytest

from faststream import BaseMiddleware
from faststream.exceptions import SetupError
from faststream.nats import ConsumerConfig, JStream, NatsBroker, PullSub, TestNatsBroker
from faststream.nats.testing import FakeProducer
from tests.brokers.base.testclient import BrokerTestclientTestcase


@pytest.mark.asyncio
class TestTestclient(BrokerTestclientTestcase):
    test_class = TestNatsBroker

    def get_broker(self, apply_types: bool = False) -> NatsBroker:
        return NatsBroker(apply_types=apply_types)

    def patch_broker(self, broker: NatsBroker) -> TestNatsBroker:
        return TestNatsBroker(broker)

    def get_fake_producer_class(self) -> type:
        return FakeProducer

    @pytest.mark.asyncio
    async def test_stream_publish(
        self,
        queue: str,
    ):
        pub_broker = NatsBroker(apply_types=False)

        @pub_broker.subscriber(queue, stream="test")
        async def m(msg): ...

        async with TestNatsBroker(pub_broker) as br:
            await br.publish("Hi!", queue, stream="test")
            m.mock.assert_called_once_with("Hi!")

    @pytest.mark.asyncio
    async def test_wrong_stream_publish(
        self,
        queue: str,
    ):
        pub_broker = NatsBroker(apply_types=False)

        @pub_broker.subscriber(queue)
        async def m(msg): ...

        async with TestNatsBroker(pub_broker) as br:
            await br.publish("Hi!", queue, stream="test")
            assert not m.mock.called

    @pytest.mark.asyncio
    async def test_rpc_conflicts_reply(self, queue):
        async with TestNatsBroker(NatsBroker()) as br:
            with pytest.raises(SetupError):
                await br.publish(
                    "",
                    queue,
                    rpc=True,
                    reply_to="response",
                )

    @pytest.mark.nats
    async def test_with_real_testclient(
        self,
        queue: str,
        event: asyncio.Event,
    ):
        broker = self.get_broker()

        @broker.subscriber(queue)
        def subscriber(m):
            event.set()

        async with TestNatsBroker(broker, with_real=True) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()

    @pytest.mark.nats
    async def test_inbox_prefix_with_real(
        self,
        queue: str,
    ):
        broker = NatsBroker(inbox_prefix="test")

        async with TestNatsBroker(broker, with_real=True) as br:
            assert br._connection._inbox_prefix == b"test"
            assert "test" in str(br._connection.new_inbox())

    async def test_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = NatsBroker(middlewares=(Middleware,))

        @broker.subscriber(queue)
        async def h1(): ...

        @broker.subscriber(queue + "1")
        async def h2(): ...

        async with TestNatsBroker(broker) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")

        assert len(routes) == 2

    @pytest.mark.nats
    async def test_real_respect_middleware(self, queue):
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = NatsBroker(middlewares=(Middleware,))

        @broker.subscriber(queue)
        async def h1(): ...

        @broker.subscriber(queue + "1")
        async def h2(): ...

        async with TestNatsBroker(broker, with_real=True) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")
            await h1.wait_call(3)
            await h2.wait_call(3)

        assert len(routes) == 2

    async def test_js_subscriber_mock(
        self,
        queue: str,
        stream: JStream,
    ):
        broker = self.get_broker()

        @broker.subscriber(queue, stream=stream)
        async def m(msg):
            pass

        async with TestNatsBroker(broker) as br:
            await br.publish("hello", queue, stream=stream.name)
            m.mock.assert_called_once_with("hello")

    async def test_js_publisher_mock(
        self,
        queue: str,
        stream: JStream,
    ):
        broker = self.get_broker()

        publisher = broker.publisher(queue + "resp")

        @publisher
        @broker.subscriber(queue, stream=stream)
        async def m(msg):
            return "response"

        async with TestNatsBroker(broker) as br:
            await br.publish("hello", queue, stream=stream.name)
            publisher.mock.assert_called_with("response")

    async def test_any_subject_routing(self):
        broker = self.get_broker()

        @broker.subscriber("test.*.subj.*")
        def subscriber(msg): ...

        async with TestNatsBroker(broker) as br:
            await br.publish("hello", "test.a.subj.b")
            subscriber.mock.assert_called_once_with("hello")

    async def test_ending_subject_routing(self):
        broker = self.get_broker()

        @broker.subscriber("test.>")
        def subscriber(msg): ...

        async with TestNatsBroker(broker) as br:
            await br.publish("hello", "test.a.subj.b")
            subscriber.mock.assert_called_once_with("hello")

    async def test_mixed_subject_routing(self):
        broker = self.get_broker()

        @broker.subscriber("*.*.subj.>")
        def subscriber(msg): ...

        async with TestNatsBroker(broker) as br:
            await br.publish("hello", "test.a.subj.b.c")
            subscriber.mock.assert_called_once_with("hello")

    async def test_consume_pull(
        self,
        queue: str,
        stream: JStream,
    ):
        broker = self.get_broker()

        @broker.subscriber(queue, stream=stream, pull_sub=PullSub(1))
        def subscriber(m): ...

        async with TestNatsBroker(broker) as br:
            await br.publish("hello", queue)
            subscriber.mock.assert_called_once_with("hello")

    async def test_consume_batch(
        self,
        queue: str,
        stream: JStream,
    ):
        broker = self.get_broker()

        @broker.subscriber(
            queue,
            stream=stream,
            pull_sub=PullSub(1, batch=True),
        )
        def subscriber(m):
            pass

        async with TestNatsBroker(broker) as br:
            await br.publish("hello", queue)
            subscriber.mock.assert_called_once_with(["hello"])

    async def test_consume_with_filter(
        self,
        queue,
    ):
        broker = self.get_broker()

        @broker.subscriber(
            config=ConsumerConfig(filter_subjects=[f"{queue}.a"]),
            stream=JStream(queue, subjects=[f"{queue}.*"]),
        )
        def subscriber(m):
            pass

        async with TestNatsBroker(broker) as br:
            await br.publish(1, f"{queue}.b")
            await br.publish(2, f"{queue}.a")
            subscriber.mock.assert_called_once_with(2)

    @pytest.mark.nats
    async def test_broker_gets_patched_attrs_within_cm(self):
        await super().test_broker_gets_patched_attrs_within_cm()

    @pytest.mark.nats
    async def test_broker_with_real_doesnt_get_patched(self):
        await super().test_broker_with_real_doesnt_get_patched()

    @pytest.mark.nats
    async def test_broker_with_real_patches_publishers_and_subscribers(
        self, queue: str
    ):
        await super().test_broker_with_real_patches_publishers_and_subscribers(queue)
