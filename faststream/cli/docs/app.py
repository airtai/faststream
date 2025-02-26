import json
import sys
import warnings
from pathlib import Path
from typing import Optional, Sequence

import typer

from faststream._compat import json_dumps, model_parse
from faststream.asyncapi.generate import get_app_schema
from faststream.asyncapi.schema import Schema
from faststream.asyncapi.site import serve_app
from faststream.cli.utils.imports import import_from_string
from faststream.exceptions import INSTALL_WATCHFILES, INSTALL_YAML

docs_app = typer.Typer(pretty_exceptions_short=True)


@docs_app.command(name="serve")
def serve(
    app: str = typer.Argument(
        ...,
        help="[python_module:FastStream] or [asyncapi.yaml/.json] - path to your application or documentation.",
    ),
    host: str = typer.Option(
        "localhost",
        help="Documentation hosting address.",
    ),
    port: int = typer.Option(
        8000,
        help="Documentation hosting port.",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        is_flag=True,
        help="Restart documentation at directory files changes.",
    ),
    app_dir: str = typer.Option(
        ".",
        "--app-dir",
        help=(
            "Look for APP in the specified directory, by adding this to the PYTHONPATH."
            " Defaults to the current working directory."
        ),
    ),
    is_factory: bool = typer.Option(
        False,
        "--factory",
        is_flag=True,
        help="Treat APP as an application factory.",
    ),
) -> None:
    """Serve project AsyncAPI schema."""
    if ":" in app:
        if app_dir:  # pragma: no branch
            sys.path.insert(0, app_dir)

        module, _ = import_from_string(app, is_factory=is_factory)

        module_parent = module.parent
        extra_extensions: Sequence[str] = ()

    else:
        module_parent = Path.cwd()
        schema_filepath = module_parent / app
        extra_extensions = (schema_filepath.suffix,)

    if reload:
        try:
            from faststream.cli.supervisors.watchfiles import WatchReloader

        except ImportError:
            warnings.warn(INSTALL_WATCHFILES, category=ImportWarning, stacklevel=1)
            _parse_and_serve(app, host, port, is_factory)

        else:
            WatchReloader(
                target=_parse_and_serve,
                args=(app, host, port, is_factory),
                reload_dirs=(str(module_parent),),
                extra_extensions=extra_extensions,
            ).run()

    else:
        _parse_and_serve(app, host, port, is_factory)


@docs_app.command(name="gen")
def gen(
    app: str = typer.Argument(
        ...,
        help="[python_module:FastStream] - path to your application.",
    ),
    yaml: bool = typer.Option(
        False,
        "--yaml",
        is_flag=True,
        help="Generate `asyncapi.yaml` schema.",
    ),
    out: Optional[str] = typer.Option(
        None,
        help="Output filename.",
    ),
    app_dir: str = typer.Option(
        ".",
        "--app-dir",
        help=(
            "Look for APP in the specified directory, by adding this to the PYTHONPATH."
            " Defaults to the current working directory."
        ),
    ),
    is_factory: bool = typer.Option(
        False,
        "--factory",
        is_flag=True,
        help="Treat APP as an application factory.",
    ),
) -> None:
    """Generate project AsyncAPI schema."""
    if app_dir:  # pragma: no branch
        sys.path.insert(0, app_dir)

    _, app_obj = import_from_string(app, is_factory=is_factory)

    raw_schema = get_app_schema(app_obj)

    if yaml:
        try:
            schema = raw_schema.to_yaml()
        except ImportError as e:  # pragma: no cover
            typer.echo(INSTALL_YAML, err=True)
            raise typer.Exit(1) from e

        name = out or "asyncapi.yaml"

        with Path(name).open("w") as f:
            f.write(schema)

    else:
        schema = raw_schema.to_jsonable()
        name = out or "asyncapi.json"

        with Path(name).open("w") as f:
            json.dump(schema, f, indent=2)

    typer.echo(f"Your project AsyncAPI scheme was placed to `{name}`")


def _parse_and_serve(
    app: str,
    host: str = "localhost",
    port: int = 8000,
    is_factory: bool = False,
) -> None:
    if ":" in app:
        _, app_obj = import_from_string(app, is_factory=is_factory)

        raw_schema = get_app_schema(app_obj)

    else:
        schema_filepath = Path.cwd() / app

        if schema_filepath.suffix == ".json":
            data = schema_filepath.read_bytes()

        elif schema_filepath.suffix == ".yaml" or schema_filepath.suffix == ".yml":
            try:
                import yaml
            except ImportError as e:  # pragma: no cover
                typer.echo(INSTALL_YAML, err=True)
                raise typer.Exit(1) from e

            with schema_filepath.open("r") as f:
                schema = yaml.safe_load(f)

            data = json_dumps(schema)

        else:
            raise ValueError(
                f"Unknown extension given - {app}; Please provide app in format [python_module:FastStream] or [asyncapi.yaml/.json] - path to your application or documentation"
            )

        raw_schema = model_parse(Schema, data)

    serve_app(raw_schema, host, port)
