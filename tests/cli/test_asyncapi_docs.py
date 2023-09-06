import json
import os
from pathlib import Path
from unittest.mock import Mock

import uvicorn
import yaml
from typer.testing import CliRunner

from faststream.cli.main import cli


def test_gen_asyncapi_json_for_kafka_app(runner: CliRunner, kafka_basic_project: Path):
    os.chdir(kafka_basic_project)
    r = runner.invoke(cli, ["docs", "gen", "basic:app"])
    assert r.exit_code == 0
    
    schema_path = kafka_basic_project / "asyncapi.json"
    assert schema_path.exists()

    with schema_path.open("r") as f:
        schema = json.load(f)

    assert schema


def test_gen_asyncapi_yaml_for_kafka_app(runner: CliRunner, kafka_basic_project: Path):
    os.chdir(kafka_basic_project)
    r = runner.invoke(cli, ["docs", "gen", "--yaml", "basic:app"])
    assert r.exit_code == 0
    
    schema_path = kafka_basic_project / "asyncapi.yaml"
    assert schema_path.exists()

    with schema_path.open("r") as f:
        schema = yaml.load(f, Loader=yaml.BaseLoader)

    assert schema


def test_gen_wrong_path(runner: CliRunner, kafka_basic_project: Path):
    os.chdir(kafka_basic_project)
    r = runner.invoke(cli, ["docs", "gen", "basic:app1"])
    assert r.exit_code == 2
    assert "Please, input module like [python_file:faststream_app_name]" in r.stdout


def test_serve_asyncapi_docs(
    runner: CliRunner,
    kafka_basic_project: Path,
    monkeypatch,
    mock: Mock,
):
    os.chdir(kafka_basic_project)
    r = runner.invoke(cli, ["docs", "gen", "basic:app"])
    app_path = f'{kafka_basic_project / "basic"}:app'

    with monkeypatch.context() as m:
        m.setattr(uvicorn, "run", mock)
        r = runner.invoke(cli, ["docs", "serve", app_path])

    assert r.exit_code == 0
    mock.assert_called_once()


def test_serve_asyncapi_json_schema(
    runner: CliRunner,
    kafka_basic_project: Path,
    monkeypatch,
    mock: Mock,
):
    os.chdir(kafka_basic_project)
    r = runner.invoke(cli, ["docs", "gen", "basic:app"])
    schema_path = kafka_basic_project / "asyncapi.json"

    with monkeypatch.context() as m:
        m.setattr(uvicorn, "run", mock)
        r = runner.invoke(cli, ["docs", "serve", str(schema_path)])

    assert r.exit_code == 0
    mock.assert_called_once()


def test_serve_asyncapi_yaml_schema(
    runner: CliRunner,
    kafka_basic_project: Path,
    monkeypatch,
    mock: Mock,
):
    os.chdir(kafka_basic_project)
    r = runner.invoke(cli, ["docs", "gen", "--yaml", "basic:app"])
    schema_path = kafka_basic_project / "asyncapi.yaml"

    with monkeypatch.context() as m:
        m.setattr(uvicorn, "run", mock)
        r = runner.invoke(cli, ["docs", "serve", str(schema_path)])

    assert r.exit_code == 0
    mock.assert_called_once()
