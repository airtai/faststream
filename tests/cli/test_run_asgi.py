import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from faststream._internal.cli.main import cli as faststream_app
from faststream.asgi import AsgiFastStream


def test_run_as_asgi(runner: CliRunner) -> None:
    app = AsgiFastStream()
    app.run = AsyncMock()

    with patch(
        "faststream._internal.cli.utils.imports._import_object_or_factory",
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
            ],
        )
        app.run.assert_awaited_once_with(
            logging.INFO,
            {"host": "0.0.0.0", "port": "8000"},
        )
        assert result.exit_code == 0


@pytest.mark.parametrize(
    "workers",
    (
        pytest.param(1),
        pytest.param(2),
        pytest.param(5),
    ),
)
def test_run_as_asgi_with_workers(runner: CliRunner, workers: int) -> None:
    app = AsgiFastStream()
    app.run = AsyncMock()

    with patch(
        "faststream._internal.cli.utils.imports._import_object_or_factory",
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
                "-w",
                str(workers),
            ],
        )
        extra = {"workers": workers} if workers > 1 else {}

        app.run.assert_awaited_once_with(
            logging.INFO,
            {"host": "0.0.0.0", "port": "8000", **extra},
        )
        assert result.exit_code == 0


def test_run_as_asgi_callable(runner: CliRunner) -> None:
    app = AsgiFastStream()
    app.run = AsyncMock()

    app_factory = Mock(return_value=app)

    with patch(
        "faststream._internal.cli.utils.imports._import_object_or_factory",
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
                "-f",
            ],
        )

        # should be called twice - for check object type and for uvicorn
        assert app_factory.called

        app.run.assert_awaited_once_with(
            logging.INFO,
            {"host": "0.0.0.0", "port": "8000"},
        )
        assert result.exit_code == 0
