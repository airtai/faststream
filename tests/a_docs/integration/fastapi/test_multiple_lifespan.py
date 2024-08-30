import pytest
from fastapi.testclient import TestClient

from tests.marks import (
    require_aiokafka,
    require_aiopika,
    require_confluent,
    require_nats,
    require_redis,
)


class BaseCase:
    def test_running(self, data):
        app, core_router, nested_router = data

        @core_router.subscriber("test1")
        async def handler(): ...

        @nested_router.subscriber("test2")
        async def handler2(): ...

        handlers1 = core_router.broker._subscribers.values()
        handlers2 = nested_router.broker._subscribers.values()

        assert len(handlers1) == 1
        assert len(handlers2) == 1

        for h in (handlers := (*handlers1, *handlers2)):
            assert not h.running

        with TestClient(app):
            for h in handlers:
                assert h.running


@pytest.mark.kafka
@require_aiokafka
class TestKafka(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.kafka.multiple_lifespan import (
            another_router,
            app,
            one_router,
        )

        return (app, one_router, another_router)


@pytest.mark.confluent
@require_confluent
class TestConfluent(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.confluent.multiple_lifespan import (
            another_router,
            app,
            one_router,
        )

        return (app, one_router, another_router)


@pytest.mark.nats
@require_nats
class TestNats(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.nats.multiple_lifespan import (
            another_router,
            app,
            one_router,
        )

        return (app, one_router, another_router)


@pytest.mark.rabbit
@require_aiopika
class TestRabbit(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.rabbit.multiple_lifespan import (
            another_router,
            app,
            one_router,
        )

        return (app, one_router, another_router)


@pytest.mark.redis
@require_redis
class TestRedis(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.redis.multiple_lifespan import (
            another_router,
            app,
            one_router,
        )

        return (app, one_router, another_router)
