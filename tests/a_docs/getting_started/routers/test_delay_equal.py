import pytest

from faststream import TestApp
from tests.marks import (
    require_aiokafka,
    require_aiopika,
    require_confluent,
    require_nats,
    require_redis,
)


@pytest.mark.asyncio
@require_aiokafka
async def test_delay_router_kafka():
    from docs.docs_src.getting_started.routers.kafka.delay_equal import (
        app,
        broker,
    )
    from docs.docs_src.getting_started.routers.kafka.router_delay import (
        broker as control_broker,
    )
    from faststream.kafka import TestKafkaBroker

    assert broker._subscribers.keys() == control_broker._subscribers.keys()
    assert broker._publishers.keys() == control_broker._publishers.keys()

    async with TestKafkaBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[
            0
        ].handler.mock.assert_called_once_with({"name": "John", "user_id": 1})

        next(iter(br._publishers.values())).mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
@require_confluent
async def test_delay_router_confluent():
    from docs.docs_src.getting_started.routers.confluent.delay_equal import (
        app,
        broker,
    )
    from docs.docs_src.getting_started.routers.confluent.router_delay import (
        broker as control_broker,
    )
    from faststream.confluent import TestKafkaBroker as TestConfluentKafkaBroker

    assert broker._subscribers.keys() == control_broker._subscribers.keys()
    assert broker._publishers.keys() == control_broker._publishers.keys()

    async with TestConfluentKafkaBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[
            0
        ].handler.mock.assert_called_once_with({"name": "John", "user_id": 1})

        next(iter(br._publishers.values())).mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
@require_aiopika
async def test_delay_router_rabbit():
    from docs.docs_src.getting_started.routers.rabbit.delay_equal import (
        app,
        broker,
    )
    from docs.docs_src.getting_started.routers.rabbit.router_delay import (
        broker as control_broker,
    )
    from faststream.rabbit import TestRabbitBroker

    assert broker._subscribers.keys() == control_broker._subscribers.keys()
    assert broker._publishers.keys() == control_broker._publishers.keys()

    async with TestRabbitBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[
            0
        ].handler.mock.assert_called_once_with({"name": "John", "user_id": 1})

        next(iter(br._publishers.values())).mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
@require_nats
async def test_delay_router_nats():
    from docs.docs_src.getting_started.routers.nats.delay_equal import (
        app,
        broker,
    )
    from docs.docs_src.getting_started.routers.nats.router_delay import (
        broker as control_broker,
    )
    from faststream.nats import TestNatsBroker

    assert broker._subscribers.keys() == control_broker._subscribers.keys()
    assert broker._publishers.keys() == control_broker._publishers.keys()

    async with TestNatsBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[
            0
        ].handler.mock.assert_called_once_with({"name": "John", "user_id": 1})

        next(iter(br._publishers.values())).mock.assert_called_once_with("Hi!")


@pytest.mark.asyncio
@require_redis
async def test_delay_router_redis():
    from docs.docs_src.getting_started.routers.redis.delay_equal import (
        app,
        broker,
    )
    from docs.docs_src.getting_started.routers.redis.router_delay import (
        broker as control_broker,
    )
    from faststream.redis import TestRedisBroker

    assert broker._subscribers.keys() == control_broker._subscribers.keys()
    assert broker._publishers.keys() == control_broker._publishers.keys()

    async with TestRedisBroker(broker) as br, TestApp(app):
        next(iter(br._subscribers.values())).calls[
            0
        ].handler.mock.assert_called_once_with({"name": "John", "user_id": 1})

        next(iter(br._publishers.values())).mock.assert_called_once_with("Hi!")
