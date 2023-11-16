from pathlib import Path

import pytest

from faststream.cli.utils.imports import import_from_string, ImportFromStringError
from faststream.app import FastStream


def test_import_wrong():
    with pytest.raises(ImportFromStringError):
        module, app = import_from_string("tests:test_object")


@pytest.mark.parametrize(
    "test_input,exp_module",
    (
        ("examples.kafka.testing:app", "examples/kafka/testing.py"),
        ("examples.nats.e01_basic:app", "examples/nats/e01_basic.py"),
        ("examples.rabbit.topic:app", "examples/rabbit/topic.py"),
    ),
)
def test_get_app_path(test_input, exp_module):
    module, app = import_from_string(test_input)
    assert isinstance(app, FastStream)
    assert Path(module.__file__) == (Path.cwd() / exp_module)


def test_get_app_path_wrong():
    with pytest.raises(ImportFromStringError):
        import_from_string("module.app")
