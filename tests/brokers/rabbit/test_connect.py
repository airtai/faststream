from typing import Type

import pytest

from faststream.rabbit import RabbitBroker
from faststream.security import SASLPlaintext
from faststream.rabbit.utils import build_url
from tests.brokers.base.connection import BrokerConnectionTestcase


@pytest.mark.rabbit
class TestConnection(BrokerConnectionTestcase):
    broker: Type[RabbitBroker] = RabbitBroker

    def get_broker_args(self, settings):
        return {"url": settings.url}

    @pytest.mark.asyncio
    async def test_init_connect_by_raw_data(self, settings):
        broker = self.broker(
            host=settings.host,
            port=settings.port,
            security=SASLPlaintext(
                username=settings.login,
                password=settings.password,
            ),
        )
        assert await broker.connect()
        await broker.close()

    @pytest.mark.asyncio
    async def test_connection_by_params(self, settings):
        broker = self.broker()
        assert await broker.connect(
            host=settings.host,
            port=settings.port,
            security=SASLPlaintext(
                username=settings.login,
                password=settings.password,
            ),
        )
        await broker.close()

    @pytest.mark.asyncio
    async def test_connect_merge_kwargs_with_priority(self, settings):
        broker = self.broker(host="fake-host", port=5677)  # kwargs will be ignored
        assert await broker.connect(
            host=settings.host,
            port=settings.port,
            security=SASLPlaintext(
                username=settings.login,
                password=settings.password,
            ),
        )
        await broker.close()

    @pytest.mark.asyncio
    async def test_connect_merge_args_and_kwargs_native(self, settings):
        broker = self.broker("fake-url")  # will be ignored
        assert await broker.connect(url=settings.url)
        await broker.close()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_input,expected",
        [
            ("amqp://root:root@localhost:5672/vh", "amqp://root:root@localhost:5672/vh"),
            ("amqp://root:root@localhost:5672/", "amqp://root:root@localhost:5672/"),
            ("amqp://root:root@localhost:5672//vh", "amqp://root:root@localhost:5672//vh"),
            ("amqp://root:root@localhost:5672/vh/vh2", "amqp://root:root@localhost:5672/vh/vh2"),
            ("amqp://root:root@localhost:5672//vh/vh2", "amqp://root:root@localhost:5672//vh/vh2")
        ]
    )
    async def test_build_url(self, test_input, expected):
        assert str(build_url(test_input)) == expected
