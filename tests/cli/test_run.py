import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from faststream._internal.application import Application
from faststream.app import FastStream
from faststream.asgi import AsgiFastStream
from faststream.cli.main import cli as faststream_app


@pytest.mark.parametrize(
    "app", [pytest.param(FastStream()), pytest.param(AsgiFastStream())]
)
def test_run(runner: CliRunner, app: Application):
    app.run = AsyncMock()

    with patch(
        "faststream.cli.utils.imports._import_obj_or_factory", return_value=(None, app)
    ):
        result = runner.invoke(
            faststream_app,
            [
                "run",
                "faststream:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
        )
        app.run.assert_awaited_once_with(
            logging.INFO, {"host": "0.0.0.0", "port": "8000"}
        )
        assert result.exit_code == 0


@pytest.mark.parametrize("workers", [1, 2, 5])
@pytest.mark.parametrize("app", [pytest.param(AsgiFastStream())])
def test_run_as_asgi_with_workers(runner: CliRunner, workers: int, app: Application):
    app.run = AsyncMock()

    with patch(
        "faststream.cli.utils.imports._import_obj_or_factory", return_value=(None, app)
    ):
        result = runner.invoke(
            faststream_app,
            [
                "run",
                "faststream:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--workers",
                str(workers),
            ],
        )
        extra = {"workers": workers} if workers > 1 else {}

        app.run.assert_awaited_once_with(
            logging.INFO, {"host": "0.0.0.0", "port": "8000", **extra}
        )
        assert result.exit_code == 0


@pytest.mark.parametrize(
    "app", [pytest.param(FastStream()), pytest.param(AsgiFastStream())]
)
def test_run_as_factory(runner: CliRunner, app: Application):
    app.run = AsyncMock()

    app_factory = Mock(return_value=app)

    with patch(
        "faststream.cli.utils.imports._import_obj_or_factory",
        return_value=(None, app_factory),
    ):
        result = runner.invoke(
            faststream_app,
            [
                "run",
                "faststream:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--factory",
            ],
        )
        app_factory.assert_called()
        app.run.assert_awaited_once_with(
            logging.INFO, {"host": "0.0.0.0", "port": "8000"}
        )
        assert result.exit_code == 0


@pytest.mark.parametrize(
    "app", [pytest.param(FastStream()), pytest.param(AsgiFastStream())]
)
def test_run_app_like_factory_but_its_fake(runner: CliRunner, app: Application):
    app.run = AsyncMock()

    with patch(
        "faststream.cli.utils.imports._import_obj_or_factory",
        return_value=(None, app),
    ):
        result = runner.invoke(
            faststream_app,
            [
                "run",
                "faststream:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--factory",
            ],
        )
        app.run.assert_not_called()
        assert result.exit_code != 0
