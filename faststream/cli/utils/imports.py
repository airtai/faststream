from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Tuple

import typer

from faststream.app import FastStream


def try_import_app(module: Path, app: str) -> FastStream:
    try:
        app_object = import_object(module, app)

    except FileNotFoundError as e:
        typer.echo(e, err=True)
        raise typer.BadParameter(
            "Please, input module like [python_file:faststream_app_name]"
        ) from e

    else:
        return app_object  # type: ignore


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
        raise ValueError(f"{app} is not a FastStream")

    module, app_name = app.split(":", 2)

    mod_path = Path.cwd()
    for i in module.split("."):
        mod_path = mod_path / i

    return mod_path, app_name
