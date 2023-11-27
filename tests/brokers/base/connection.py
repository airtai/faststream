import os
from typing import Type

import pytest

from faststream.broker.core.abc import BrokerUsecase


class BrokerConnectionTestcase:
    broker: Type[BrokerUsecase]

    def get_broker_args(self, settings):
        return (settings.url,), {}

    async def ping(self, broker) -> bool:
        return True

    @pytest.mark.asyncio
    async def test_close_before_start(self, async_mock):
        br = self.broker()
        assert br._connection is None
        await br.close()
        br._connection = async_mock
        await br._close()
        assert not br.started

    @pytest.mark.asyncio
    async def test_warning(self, broker: BrokerUsecase):
        del os.environ["PYTEST_CURRENT_TEST"]

        async with broker:
            await broker.start()
            assert broker.started
            with pytest.warns(RuntimeWarning):
                broker.subscriber("test")
        assert not broker.started

    @pytest.mark.asyncio
    async def test_init_connect_by_url(self, settings):
        args, kwargs = self.get_broker_args(settings)
        broker = self.broker(*args, **kwargs)
        assert await broker.connect()
        assert await self.ping(broker)
        await broker.close()

    @pytest.mark.asyncio
    async def test_connection_by_url(self, settings):
        args, kwargs = self.get_broker_args(settings)
        broker = self.broker()
        assert await broker.connect(*args, **kwargs)
        assert await self.ping(broker)
        await broker.close()

    @pytest.mark.asyncio
    async def test_connect_by_url_priority(self, settings):
        args, kwargs = self.get_broker_args(settings)
        broker = self.broker("wrong_url")
        assert await broker.connect(*args, **kwargs)
        assert await self.ping(broker)
        await broker.close()

    @pytest.mark.asyncio
    async def test_connect_merge_args_and_kwargs_base(self, settings):
        args, kwargs = self.get_broker_args(settings)
        broker = self.broker(*args)
        assert await broker.connect(**kwargs)
        assert await self.ping(broker)
        await broker.close()
