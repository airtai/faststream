from pathlib import Path

import pytest
from typer import BadParameter

from faststream.app import FastStream
from faststream.cli.utils.imports import get_app_path, import_from_string, import_object


def test_import_wrong():
    dir, app = get_app_path("tests:test_object")
    with pytest.raises(FileNotFoundError):
        import_object(dir, app)


@pytest.mark.parametrize(
    "test_input,exp_module,exp_app",
    (
        pytest.param("module:app", "module", "app"),
        pytest.param("module.module.module:app", "module/module/module", "app"),
    ),
)
def test_get_app_path(test_input, exp_module, exp_app):
    dir, app = get_app_path(test_input)
    assert app == exp_app
    assert dir == Path.cwd() / exp_module


def test_get_app_path_wrong():
    with pytest.raises(ValueError):
        get_app_path("module.app")


def test_import_from_string_import_wrong():
    with pytest.raises(BadParameter):
        module, app = import_from_string("tests:test_object")


@pytest.mark.parametrize(
    "test_input,exp_module",
    (
        pytest.param("examples.kafka.testing:app", "examples/kafka/testing.py"),
        pytest.param("examples.nats.e01_basic:app", "examples/nats/e01_basic.py"),
        pytest.param("examples.rabbit.topic:app", "examples/rabbit/topic.py"),
    ),
)
def test_import_from_string(test_input, exp_module):
    module, app = import_from_string(test_input)
    assert isinstance(app, FastStream)
    assert module == (Path.cwd() / exp_module).parent


@pytest.mark.parametrize(
    "test_input,exp_module",
    (
        pytest.param("examples.kafka:app", "examples/kafka/__init__.py"),
        pytest.param("examples.nats:app", "examples/nats/__init__.py"),
        pytest.param("examples.rabbit:app", "examples/rabbit/__init__.py"),
    ),
)
def test_import_module(test_input, exp_module):
    module, app = import_from_string(test_input)
    assert isinstance(app, FastStream)
    assert module == (Path.cwd() / exp_module).parent


def test_import_from_string_wrong():
    with pytest.raises(BadParameter):
        import_from_string("module.app")
