from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Tuple

import typer

from propan.app import PropanApp


def try_import_propan(module: Path, app: str) -> PropanApp:
    try:
        propan_app = import_object(module, app)

    except FileNotFoundError as e:
        typer.echo(e, err=True)
        raise typer.BadParameter(
            "Please, input module like [python_file:propan_app_name]"
        ) from e

    else:
        return propan_app  # type: ignore


def import_object(module: Path, app: str) -> object:
    spec = spec_from_file_location(
        "mode",
        f"{module}.py",
        submodule_search_locations=[str(module.parent.absolute())],
    )

    if spec is None:  # pragma: no cover
        raise FileNotFoundError(module)

    mod = module_from_spec(spec)
    loader = spec.loader

    if loader is None:  # pragma: no cover
        raise ValueError(f"{spec} has no loader")

    loader.exec_module(mod)

    try:
        obj = getattr(mod, app)
    except AttributeError as e:
        raise FileNotFoundError(module) from e

    return obj


def get_app_path(app: str) -> Tuple[Path, str]:
    if ":" not in app:
        raise ValueError(f"{app} is not a PropanApp")

    module, propan_app = app.split(":", 2)

    mod_path = Path.cwd()
    for i in module.split("."):
        mod_path = mod_path / i

    return mod_path, propan_app
