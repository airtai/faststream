import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from faststream import FastStream


@pytest.fixture()
def broker():
    # separate import from e2e tests
    from faststream.rabbit import RabbitBroker

    yield RabbitBroker()


@pytest.fixture()
def app_without_logger(broker):
    return FastStream(broker, None)


@pytest.fixture()
def app_without_broker():
    return FastStream()


@pytest.fixture()
def app(broker):
    return FastStream(broker)


@pytest.fixture(scope="session")
def runner() -> CliRunner:
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


@pytest.fixture()
def kafka_basic_project(request, tmp_path) -> Path:
    source_file = Path(request.config.rootdir) / "docs/docs_src/kafka/basic/basic.py"
    dest_file = tmp_path / "basic.py"

    shutil.copy(str(source_file), str(dest_file))

    yield tmp_path
