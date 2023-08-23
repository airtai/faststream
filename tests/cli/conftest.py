import pytest
from typer.testing import CliRunner

from propan import PropanApp


@pytest.fixture()
def broker():
    # separate import from e2e tests
    from propan.rabbit import RabbitBroker

    yield RabbitBroker()


@pytest.fixture()
def app_without_logger(broker):
    return PropanApp(broker, None)


@pytest.fixture()
def app_without_broker():
    return PropanApp()


@pytest.fixture()
def app(broker):
    return PropanApp(broker)


@pytest.fixture(scope="session")
def runner() -> CliRunner:
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner
