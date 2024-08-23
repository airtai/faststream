import pytest

from faststream import FastStream


@pytest.fixture
def broker():
    # separate import from e2e tests
    from faststream.rabbit import RabbitBroker

    return RabbitBroker()


@pytest.fixture
def app_without_logger(broker):
    return FastStream(broker, None)


@pytest.fixture
def app_without_broker():
    return FastStream()


@pytest.fixture
def app(broker):
    return FastStream(broker)
