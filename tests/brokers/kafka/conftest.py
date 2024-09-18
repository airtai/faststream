from dataclasses import dataclass

import pytest

from faststream.kafka import KafkaRouter


@dataclass
class Settings:
    url = "localhost:9092"


@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixture
def router():
    return KafkaRouter()
