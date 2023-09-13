import pytest

from faststream.rabbit import RabbitBroker
from tests.brokers.base.connection import BrokerConnectionTestcase


@pytest.mark.rabbit
class TestConnection(BrokerConnectionTestcase):
    broker = RabbitBroker

    @pytest.mark.asyncio
    async def test_init_connect_by_raw_data(self, settings):
        broker = self.broker(
            host=settings.host,
            login=settings.login,
            password=settings.password,
            port=settings.port,
        )
        assert await broker.connect()
        await broker.close()

    @pytest.mark.asyncio
    async def test_connection_by_params(self, settings):
        broker = self.broker()
        assert await broker.connect(
            host=settings.host,
            login=settings.login,
            password=settings.password,
            port=settings.port,
        )
        await broker.close()

    @pytest.mark.asyncio
    async def test_connect_merge_kwargs_with_priority(self, settings):
        broker = self.broker(host="fake-host", port=5677)  # kwargs will be ignored
        assert await broker.connect(
            host=settings.host,
            login=settings.login,
            password=settings.password,
            port=settings.port,
        )
        await broker.close()

    @pytest.mark.asyncio
    async def test_connect_merge_args_and_kwargs_native(self, settings):
        broker = self.broker("fake-url")  # will be ignored
        assert await broker.connect(url=settings.url)
        await broker.close()
