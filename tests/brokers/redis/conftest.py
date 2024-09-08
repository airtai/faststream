from dataclasses import dataclass

import pytest
import pytest_asyncio

from faststream.redis import (
    RedisBroker,
    RedisRouter,
    TestRedisBroker,
)


@dataclass
class Settings:
    url = "redis://localhost:6379"  # pragma: allowlist secret
    host = "localhost"
    port = 6379


@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixture
def router():
    return RedisRouter()


@pytest_asyncio.fixture()
async def broker(settings):
    broker = RedisBroker(settings.url, apply_types=False)
    async with broker:
        yield broker


@pytest_asyncio.fixture()
async def full_broker(settings):
    broker = RedisBroker(settings.url)
    async with broker:
        yield broker


@pytest_asyncio.fixture()
async def test_broker():
    broker = RedisBroker()
    async with TestRedisBroker(broker) as br:
        yield br
