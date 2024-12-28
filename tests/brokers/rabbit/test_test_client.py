import asyncio

import pytest

from faststream import BaseMiddleware
from faststream.exceptions import SubscriberNotFound
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.annotations import RabbitMessage
from faststream.rabbit.testing import FakeProducer, _is_handler_matches, apply_pattern
from tests.brokers.base.testclient import BrokerTestclientTestcase

from .basic import RabbitMemoryTestcaseConfig


@pytest.mark.asyncio()
class TestTestclient(RabbitMemoryTestcaseConfig, BrokerTestclientTestcase):
    @pytest.mark.rabbit()
    async def test_with_real_testclient(
        self,
        queue: str,
    ) -> None:
        event = asyncio.Event()

        broker = self.get_broker()

        @broker.subscriber(queue)
        def subscriber(m) -> None:
            event.set()

        async with self.patch_broker(broker, with_real=True) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(br.publish("hello", queue)),
                    asyncio.create_task(event.wait()),
                ),
                timeout=3,
            )

        assert event.is_set()

    async def test_respect_routing_key(self) -> None:
        broker = self.get_broker()

        publisher = broker.publisher(
            exchange=RabbitExchange("test", type=ExchangeType.TOPIC),
            routing_key="up",
        )

        async with self.patch_broker(broker):
            await publisher.publish("Hi!")

            publisher.mock.assert_called_once_with("Hi!")

    async def test_direct(
        self,
        queue: str,
    ) -> None:
        broker = self.get_broker()

        @broker.subscriber(queue)
        async def handler(m) -> int:
            return 1

        @broker.subscriber(queue + "1", exchange="test")
        async def handler2(m) -> int:
            return 2

        async with self.patch_broker(broker) as br:
            await br.start()

            assert await (await br.request("", queue)).decode() == 1
            assert (
                await (await br.request("", queue + "1", exchange="test")).decode() == 2
            )

            with pytest.raises(SubscriberNotFound):
                await br.request("", exchange="test2")

    async def test_fanout(
        self,
        queue: str,
        mock,
    ) -> None:
        broker = self.get_broker()

        exch = RabbitExchange("test", type=ExchangeType.FANOUT)

        @broker.subscriber(queue, exchange=exch)
        async def handler(m) -> None:
            mock()

        async with self.patch_broker(broker) as br:
            await br.request("", exchange=exch)

            with pytest.raises(SubscriberNotFound):
                await br.request("", exchange="test2")

            assert mock.call_count == 1

    async def test_any_topic_routing(self) -> None:
        broker = self.get_broker()

        exch = RabbitExchange("test", type=ExchangeType.TOPIC)

        @broker.subscriber(
            RabbitQueue("test", routing_key="test.*.subj.*"),
            exchange=exch,
        )
        def subscriber(msg) -> None: ...

        async with self.patch_broker(broker) as br:
            await br.publish("hello", "test.a.subj.b", exchange=exch)
            subscriber.mock.assert_called_once_with("hello")

    async def test_ending_topic_routing(self) -> None:
        broker = self.get_broker()

        exch = RabbitExchange("test", type=ExchangeType.TOPIC)

        @broker.subscriber(
            RabbitQueue("test", routing_key="test.#"),
            exchange=exch,
        )
        def subscriber(msg) -> None: ...

        async with self.patch_broker(broker) as br:
            await br.publish("hello", "test.a.subj.b", exchange=exch)
            subscriber.mock.assert_called_once_with("hello")

    async def test_mixed_topic_routing(self) -> None:
        broker = self.get_broker()

        exch = RabbitExchange("test", type=ExchangeType.TOPIC)

        @broker.subscriber(
            RabbitQueue("test", routing_key="*.*.subj.#"),
            exchange=exch,
        )
        def subscriber(msg) -> None: ...

        async with self.patch_broker(broker) as br:
            await br.publish("hello", "test.a.subj.b.c", exchange=exch)
            subscriber.mock.assert_called_once_with("hello")

    async def test_header(self) -> None:
        broker = self.get_broker()

        q1 = RabbitQueue(
            "test-queue-2",
            bind_arguments={"key": 2, "key2": 2, "x-match": "any"},
        )
        q2 = RabbitQueue(
            "test-queue-3",
            bind_arguments={"key": 2, "key2": 2, "x-match": "all"},
        )
        q3 = RabbitQueue(
            "test-queue-4",
            bind_arguments={},
        )
        exch = RabbitExchange("exchange", type=ExchangeType.HEADERS)

        @broker.subscriber(q2, exch)
        async def handler2(msg) -> int:
            return 2

        @broker.subscriber(q1, exch)
        async def handler(msg) -> int:
            return 1

        @broker.subscriber(q3, exch)
        async def handler3(msg) -> int:
            return 3

        async with self.patch_broker(broker) as br:
            assert (
                await (
                    await br.request(exchange=exch, headers={"key": 2, "key2": 2})
                ).decode()
                == 2
            )
            assert (
                await (await br.request(exchange=exch, headers={"key": 2})).decode()
                == 1
            )
            assert await (await br.request(exchange=exch, headers={})).decode() == 3

    async def test_consume_manual_ack(
        self,
        queue: str,
        exchange: RabbitExchange,
    ) -> None:
        broker = self.get_broker(apply_types=True)

        consume = asyncio.Event()
        consume2 = asyncio.Event()
        consume3 = asyncio.Event()

        @broker.subscriber(queue=queue, exchange=exchange)
        async def handler(msg: RabbitMessage) -> None:
            await msg.raw_message.ack()
            consume.set()

        @broker.subscriber(queue=queue + "1", exchange=exchange)
        async def handler2(msg: RabbitMessage):
            await msg.raw_message.nack()
            consume2.set()
            raise ValueError

        @broker.subscriber(queue=queue + "2", exchange=exchange)
        async def handler3(msg: RabbitMessage):
            await msg.raw_message.reject()
            consume3.set()
            raise ValueError

        async with self.patch_broker(broker) as br:
            await asyncio.wait(
                (
                    asyncio.create_task(
                        br.publish("hello", queue=queue, exchange=exchange),
                    ),
                    asyncio.create_task(
                        br.publish("hello", queue=queue + "1", exchange=exchange),
                    ),
                    asyncio.create_task(
                        br.publish("hello", queue=queue + "2", exchange=exchange),
                    ),
                    asyncio.create_task(consume.wait()),
                    asyncio.create_task(consume2.wait()),
                    asyncio.create_task(consume3.wait()),
                ),
                timeout=3,
            )

        assert consume.is_set()
        assert consume2.is_set()
        assert consume3.is_set()

    async def test_respect_middleware(self, queue) -> None:
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = self.get_broker(middlewares=(Middleware,))

        @broker.subscriber(queue)
        async def h1(msg) -> None: ...

        @broker.subscriber(queue + "1")
        async def h2(msg) -> None: ...

        async with self.patch_broker(broker) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")

        assert len(routes) == 2

    @pytest.mark.rabbit()
    async def test_real_respect_middleware(self, queue) -> None:
        routes = []

        class Middleware(BaseMiddleware):
            async def on_receive(self) -> None:
                routes.append(None)
                return await super().on_receive()

        broker = self.get_broker(middlewares=(Middleware,))

        @broker.subscriber(queue)
        async def h1(msg) -> None: ...

        @broker.subscriber(queue + "1")
        async def h2(msg) -> None: ...

        async with self.patch_broker(broker, with_real=True) as br:
            await br.publish("", queue)
            await br.publish("", queue + "1")
            await h1.wait_call(3)
            await h2.wait_call(3)

        assert len(routes) == 2

    @pytest.mark.rabbit()
    async def test_broker_gets_patched_attrs_within_cm(self) -> None:
        await super().test_broker_gets_patched_attrs_within_cm(FakeProducer)

    @pytest.mark.rabbit()
    async def test_broker_with_real_doesnt_get_patched(self) -> None:
        await super().test_broker_with_real_doesnt_get_patched()

    @pytest.mark.rabbit()
    async def test_broker_with_real_patches_publishers_and_subscribers(
        self,
        queue: str,
    ) -> None:
        await super().test_broker_with_real_patches_publishers_and_subscribers(queue)


@pytest.mark.parametrize(
    ("pattern", "current", "result"),
    (
        pytest.param("#", "1.2.3", True, id="#"),
        pytest.param("*", "1", True, id="*"),
        pytest.param("*", "1.2", False, id="* - broken"),
        pytest.param("test.*", "test.1", True, id="test.*"),
        pytest.param("test.#", "test.1", True, id="test.#"),
        pytest.param("#.test.#", "1.2.test.1.2", True, id="#.test.#"),
        pytest.param("#.test.*", "1.2.test.1", True, id="#.test.*"),
        pytest.param("#.test.*.*", "1.2.test.1.2", True, id="#.test.*."),
        pytest.param("#.test.*.*.*", "1.2.test.1.2", False, id="#.test.*.*.* - broken"),
        pytest.param(
            "#.test.*.test.#",
            "1.2.test.1.test.1.2",
            True,
            id="#.test.*.test.#",
        ),
        pytest.param("#.*.test", "1.2.2.test", True, id="#.*.test"),
        pytest.param("#.2.*.test", "1.2.2.test", True, id="#.2.*.test"),
        pytest.param("#.*.*.test", "1.2.2.test", True, id="#.*.*.test"),
        pytest.param("*.*.*.test", "1.2.test", False, id="*.*.*.test - broken"),
        pytest.param("#.*.*.test", "1.2.test", False, id="#.*.*.test - broken"),
    ),
)
def test(pattern: str, current: str, result: bool) -> None:
    assert apply_pattern(pattern, current) == result


exch_direct = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.DIRECT)
exch_fanout = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.FANOUT)
exch_topic = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.TOPIC)
exch_headers = RabbitExchange("exchange", auto_delete=True, type=ExchangeType.HEADERS)
reqular_queue = RabbitQueue("test-reqular-queue", auto_delete=True)
routing_key_queue = RabbitQueue("test-routing-key-queue", auto_delete=True, routing_key="*.info")
one_key_queue = RabbitQueue("test-one-key-queue", auto_delete=True, bind_arguments={"key": 1})
any_keys_queue = RabbitQueue("test-any-keys-queue", auto_delete=True, bind_arguments={"key": 2, "key2": 2, "x-match": "any"})
all_keys_queue = RabbitQueue("test-all-keys-queue", auto_delete=True, bind_arguments={"key": 2, "key2": 2, "x-match": "all"})

broker = RabbitBroker()


@pytest.mark.parametrize(("queue", "exchange", "routing_key", "headers", "expected_result"),
                         (pytest.param(reqular_queue, exch_direct, "test-q-1", {}, True,
                                       id="direct match"),
                          pytest.param(reqular_queue, exch_direct, "test-q-1111", {}, False,
                                       id="direct no match"),
                          pytest.param(reqular_queue, exch_fanout, "any-key", {}, True,
                                       id="fanout match"),
                          pytest.param(routing_key_queue, exch_topic, "log.info", {}, True,
                                       id="topic match"),
                          pytest.param(routing_key_queue, exch_topic, "log.debug", {}, False,
                                       id="topic no match"),
                          pytest.param(one_key_queue, exch_headers, "any-key", {"key": 1}, True,
                                       id="headers match"),
                          pytest.param(one_key_queue, exch_headers, "any-key", {"key": 3333}, False,
                                       id="headers no match"),
                          pytest.param(any_keys_queue, exch_headers, "any-key", {"key2": 2}, True,
                                       id="headers any match"),
                          pytest.param(any_keys_queue, exch_headers, "any-key", {"key2": 33333}, False,
                                       id="headers any no match"),
                          pytest.param(all_keys_queue, exch_headers, "any-key", {"key": 2, "key2": 2}, True,
                                       id="headers all match"),
                          pytest.param(all_keys_queue, exch_headers, "any-key", {"key": 1, "key2": 2}, False,
                                       id="headers all no match"),
                          ))
def test_in_memory_routing(queue: str, exchange: RabbitExchange, routing_key: str, headers: dict[str,Any],
                           expected_result: bool):
    subscriber = broker.subscriber(queue, exchange)
    assert _is_handler_matches(subscriber, routing_key, headers, exchange) == expected_result
