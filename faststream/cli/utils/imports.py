import importlib
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import TYPE_CHECKING, Tuple

import typer

from faststream.exceptions import SetupError

if TYPE_CHECKING:
    from faststream.app import FastStream


def try_import_app(module: Path, app: str) -> "FastStream":
    """Tries to import a FastStream app from a module."""
    try:
        app_object = import_object(module, app)

    except FileNotFoundError as e:
        typer.echo(e, err=True)
        raise typer.BadParameter(
            "Please, input module like [python_file:faststream_app_name] or [module:attribute]"
        ) from e

    else:
        return app_object  # type: ignore


def import_object(module: Path, app: str) -> object:
    """Import an object from a module."""
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
        raise SetupError(f"{spec} has no loader")

    loader.exec_module(mod)

    try:
        obj = getattr(mod, app)
    except AttributeError as e:
        raise FileNotFoundError(module) from e

    return obj


def get_app_path(app: str) -> Tuple[Path, str]:
    """Get the application path."""
    if ":" not in app:
        raise SetupError(f"`{app}` is not a FastStream")

    module, app_name = app.split(":", 2)

    mod_path = Path.cwd()
    for i in module.split("."):
        mod_path = mod_path / i

    return mod_path, app_name


def import_from_string(import_str: str) -> Tuple[Path, "FastStream"]:
    """Import FastStream application from module specified by a string."""
    if not isinstance(import_str, str):
        raise typer.BadParameter("Given value is not of type string")

    module_str, _, attrs_str = import_str.partition(":")
    if not module_str or not attrs_str:
        raise typer.BadParameter(
            f'Import string "{import_str}" must be in format "<module>:<attribute>"'
        )

    try:
        module = importlib.import_module(  # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
            module_str
        )

    except ModuleNotFoundError:
        module_path, app_name = get_app_path(import_str)
        instance = try_import_app(module_path, app_name)

    else:
        attr = module
        try:
            for attr_str in attrs_str.split("."):
                attr = getattr(attr, attr_str)
            instance = attr  # type: ignore[assignment]

        except AttributeError as e:
            typer.echo(e, err=True)
            raise typer.BadParameter(
                f'Attribute "{attrs_str}" not found in module "{module_str}".'
            ) from e

        if module.__file__:
            module_path = Path(module.__file__).resolve().parent
        else:
            module_path = Path.cwd()

    return module_path, instance
