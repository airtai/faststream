from pathlib import Path

import pytest

from faststream.cli.utils.imports import get_app_path, import_object


def test_import_wrong():
    dir, app = get_app_path("tests:test_object")
    with pytest.raises(FileNotFoundError) as excinfo:
        import_object(dir, app)

    assert f"{dir}.py" in str(excinfo.value)


@pytest.mark.parametrize(
    "test_input,exp_module,exp_app",
    (
        ("module:app", "module", "app"),
        ("module.module.module:app", "module/module/module", "app"),
    ),
)
def test_get_app_path(test_input, exp_module, exp_app):
    dir, app = get_app_path(test_input)
    assert app == exp_app
    assert dir == Path.cwd() / exp_module


def test_get_app_path_wrong():
    with pytest.raises(ValueError):
        get_app_path("module.app")
