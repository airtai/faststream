import pytest
from pydantic import ValidationError

from faststream.kafka import TestKafkaBroker
from faststream.nats import TestNatsBroker
from faststream.rabbit import TestRabbitBroker
from faststream.redis import TestRedisBroker
from tests.marks import python39


@pytest.mark.asyncio
@python39
class BaseCase:
    async def test_handle(self, setup):
        broker, handle = setup

        async with self.test_class(broker) as br:
            await br.publish({"name": "John", "user_id": 1}, "test")
            handle.mock.assert_called_once_with({"name": "John", "user_id": 1})

        assert handle.mock is None

    async def test_validation_error(self, setup):
        broker, handle = setup

        async with self.test_class(broker) as br:
            with pytest.raises(ValidationError):
                await br.publish("wrong message", "test")

            handle.mock.assert_called_once_with("wrong message")


class TestKafka(BaseCase):
    test_class = TestKafkaBroker

    @pytest.fixture(scope="class")
    def setup(self):
        from docs.docs_src.getting_started.subscription.kafka.pydantic_annotated_fields import (
            broker,
            handle,
        )

        return (broker, handle)


class TestRabbit(BaseCase):
    test_class = TestRabbitBroker

    @pytest.fixture(scope="class")
    def setup(self):
        from docs.docs_src.getting_started.subscription.rabbit.pydantic_annotated_fields import (
            broker,
            handle,
        )

        return (broker, handle)


class TestNats(BaseCase):
    test_class = TestNatsBroker

    @pytest.fixture(scope="class")
    def setup(self):
        from docs.docs_src.getting_started.subscription.nats.pydantic_annotated_fields import (
            broker,
            handle,
        )

        return (broker, handle)


class TestRedis(BaseCase):
    test_class = TestRedisBroker

    @pytest.fixture(scope="class")
    def setup(self):
        from docs.docs_src.getting_started.subscription.redis.pydantic_annotated_fields import (
            broker,
            handle,
        )

        return (broker, handle)
