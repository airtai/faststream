import json
from pathlib import Path
from unittest.mock import Mock

import uvicorn
import yaml
from typer.testing import CliRunner

from faststream.cli.main import cli


def test_gen_asyncapi_json_for_kafka_app(runner: CliRunner, kafka_basic_project: Path):
    r = runner.invoke(cli, ["docs", "gen", kafka_basic_project])
    assert r.exit_code == 0

    schema_path = Path.cwd() / "asyncapi.json"
    assert schema_path.exists()

    with schema_path.open("r") as f:
        schema = json.load(f)

    assert schema
    schema_path.unlink()


def test_gen_asyncapi_yaml_for_kafka_app(runner: CliRunner, kafka_basic_project: Path):
    r = runner.invoke(cli, ["docs", "gen", "--yaml", kafka_basic_project])
    assert r.exit_code == 0

    schema_path = Path.cwd() / "asyncapi.yaml"
    assert schema_path.exists()

    with schema_path.open("r") as f:
        schema = yaml.load(f, Loader=yaml.BaseLoader)

    assert schema
    schema_path.unlink()


def test_gen_wrong_path(runner: CliRunner):
    r = runner.invoke(cli, ["docs", "gen", "basic:app1"])
    assert r.exit_code == 2
    assert "Please, input module like [python_file:faststream_app_name]" in r.stdout


def test_serve_asyncapi_docs(
    runner: CliRunner,
    kafka_basic_project: Path,
    monkeypatch,
    mock: Mock,
):
    with monkeypatch.context() as m:
        m.setattr(uvicorn, "run", mock)
        r = runner.invoke(cli, ["docs", "serve", kafka_basic_project])

    assert r.exit_code == 0
    mock.assert_called_once()


def test_serve_asyncapi_json_schema(
    runner: CliRunner,
    kafka_basic_project: Path,
    monkeypatch,
    mock: Mock,
):
    r = runner.invoke(cli, ["docs", "gen", kafka_basic_project])
    schema_path = Path.cwd() / "asyncapi.json"

    with monkeypatch.context() as m:
        m.setattr(uvicorn, "run", mock)
        r = runner.invoke(cli, ["docs", "serve", str(schema_path)])

    assert r.exit_code == 0
    mock.assert_called_once()

    schema_path.unlink()


def test_serve_asyncapi_yaml_schema(
    runner: CliRunner,
    kafka_basic_project: Path,
    monkeypatch,
    mock: Mock,
):
    r = runner.invoke(cli, ["docs", "gen", "--yaml", kafka_basic_project])
    schema_path = Path.cwd() / "asyncapi.yaml"

    with monkeypatch.context() as m:
        m.setattr(uvicorn, "run", mock)
        r = runner.invoke(cli, ["docs", "serve", str(schema_path)])

    assert r.exit_code == 0
    mock.assert_called_once()

    schema_path.unlink()
