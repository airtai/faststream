import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from faststream.__about__ import __version__
from faststream.utils import context as global_context


@pytest.hookimpl(tryfirst=True)
def pytest_keyboard_interrupt(excinfo):  # pragma: no cover
    pytest.mark.skip("Interrupted Test Session")


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker("all")


@pytest.fixture()
def queue():
    return str(uuid4())


@pytest.fixture()
def event():
    return asyncio.Event()


@pytest.fixture(scope="session")
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def mock():
    m = MagicMock()
    yield m
    m.reset_mock()


@pytest.fixture()
def async_mock():
    m = AsyncMock()
    yield m
    m.reset_mock()


@pytest.fixture(scope="session")
def version():
    return __version__


@pytest.fixture()
def context():
    yield global_context
    global_context.clear()


@pytest.fixture()
def kafka_basic_project():
    return "docs.docs_src.kafka.basic.basic:app"


@pytest.fixture(scope="session", autouse=True)
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
