from dataclasses import dataclass

import pytest
import pytest_asyncio

from faststream.nats import (
    JStream,
    NatsBroker,
    NatsRouter,
    TestNatsBroker,
)


@dataclass
class Settings:
    url = "nats://localhost:4222"  # pragma: allowlist secret


@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixture
def stream(queue):
    return JStream(queue)


@pytest.fixture
def router():
    return NatsRouter()


@pytest_asyncio.fixture()
async def broker(settings):
    broker = NatsBroker([settings.url], apply_types=False)
    async with broker:
        yield broker


@pytest_asyncio.fixture()
async def full_broker(settings):
    broker = NatsBroker([settings.url])
    async with broker:
        yield broker


@pytest_asyncio.fixture()
async def test_broker():
    broker = NatsBroker()
    async with TestNatsBroker(broker) as br:
        yield br
