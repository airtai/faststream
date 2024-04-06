import pytest
from fastapi.testclient import TestClient


class BaseCase:
    def test_running(self, data):
        app, broker = data

        handlers = broker._subscribers.values()

        assert len(handlers) == 2
        for h in handlers:
            assert not h.running

        with TestClient(app):
            for h in handlers:
                assert h.running


@pytest.mark.kafka()
class TestKafka(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.kafka.multiple import app, core_router

        return (app, core_router.broker)


@pytest.mark.confluent()
class TestConfluent(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.confluent.multiple import (
            app,
            core_router,
        )

        return (app, core_router.broker)


@pytest.mark.nats()
class TestNats(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.nats.multiple import app, core_router

        return (app, core_router.broker)


@pytest.mark.rabbit()
class TestRabbit(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.rabbit.multiple import app, core_router

        return (app, core_router.broker)


@pytest.mark.redis()
class TestRedis(BaseCase):
    @pytest.fixture(scope="class")
    def data(self):
        from docs.docs_src.integrations.fastapi.redis.multiple import app, core_router

        return (app, core_router.broker)
