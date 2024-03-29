import os
from typing import Type

import pytest

from faststream.broker.core.usecase import BrokerUsecase


class BrokerConnectionTestcase:
    broker: Type[BrokerUsecase]

    def get_broker_args(self, settings):
        return {}

    async def ping(self, broker) -> bool:
        return True

    @pytest.mark.asyncio()
    async def test_close_before_start(self, async_mock):
        br = self.broker()
        assert br._connection is None
        await br.close()
        br._connection = async_mock
        await br._close()
        assert not br.running

    @pytest.mark.asyncio()
    async def test_init_connect_by_url(self, settings):
        kwargs = self.get_broker_args(settings)
        broker = self.broker(**kwargs)
        assert await broker.connect()
        assert await self.ping(broker)
        await broker.close()

    @pytest.mark.asyncio()
    async def test_connection_by_url(self, settings):
        kwargs = self.get_broker_args(settings)
        broker = self.broker()
        assert await broker.connect(**kwargs)
        assert await self.ping(broker)
        await broker.close()

    @pytest.mark.asyncio()
    async def test_connect_by_url_priority(self, settings):
        kwargs = self.get_broker_args(settings)
        broker = self.broker("wrong_url")
        assert await broker.connect(**kwargs)
        assert await self.ping(broker)
        await broker.close()
