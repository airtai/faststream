from dataclasses import dataclass
from uuid import uuid4

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


@pytest.fixture()
def router():
    return KafkaRouter()


@pytest_asyncio.fixture
@pytest.mark.confluent()
async def broker(settings):
    broker = KafkaBroker(settings.url, apply_types=False)
    async with broker:
        yield broker


@pytest_asyncio.fixture(scope="session")
@pytest.mark.confluent()
async def confluent_kafka_topic(settings):
    topic = str(uuid4())

    # config = {"bootstrap.servers": settings.url}

    # p = Producer(config)
    # to_send = f"test msg - {topic}"
    # p.produce(topic, to_send.encode("utf-8"))
    # p.flush()

    # while True:
    #     c = Consumer(
    #         {
    #             **config,
    #             **{"group.id": f"{topic}-group", "auto.offset.reset": "earliest"},
    #         }
    #     )
    #     c.subscribe([topic])
    #     msg = c.poll()
    #     if msg is None or msg.error():
    #         continue
    #     if msg.value().decode("utf-8") == to_send:
    #         break
    #     c.close()
    #     await asyncio.sleep(1)

    return topic


@pytest_asyncio.fixture
@pytest.mark.confluent()
async def full_broker(settings):
    broker = KafkaBroker(settings.url)
    async with broker:
        yield broker


@pytest_asyncio.fixture
async def test_broker():
    broker = KafkaBroker()
    async with TestKafkaBroker(broker) as br:
        yield br
