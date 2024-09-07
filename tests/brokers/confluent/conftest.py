from dataclasses import dataclass

import pytest
import pytest_asyncio

from faststream.confluent import KafkaBroker, KafkaRouter, TestKafkaBroker


@dataclass
class Settings:
    """A class to represent the settings for the Kafka broker."""

    url = "localhost:9092"


@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixture
def router():
    return KafkaRouter()


@pytest_asyncio.fixture()
async def broker(settings):
    broker = KafkaBroker(settings.url, apply_types=False)
    async with broker:
        yield broker


@pytest_asyncio.fixture()
async def full_broker(settings):
    broker = KafkaBroker(settings.url)
    async with broker:
        yield broker


@pytest_asyncio.fixture()
async def test_broker():
    broker = KafkaBroker()
    async with TestKafkaBroker(broker) as br:
        yield br
