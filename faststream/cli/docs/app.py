import json
import warnings
from pathlib import Path
from typing import Optional, Sequence

import typer

from faststream.__about__ import INSTALL_WATCHFILES, INSTALL_YAML
from faststream._compat import model_parse
from faststream.asyncapi.generate import get_app_schema
from faststream.asyncapi.schema import Schema
from faststream.asyncapi.site import serve_app
from faststream.cli.utils.imports import import_from_string

docs_app = typer.Typer(pretty_exceptions_short=True)


@docs_app.command(name="serve")
def serve(
    app: str = typer.Argument(
        ...,
        help="[python_module:FastStream] or [asyncapi.yaml/.json] - path to your application or documentation",
    ),
    host: str = typer.Option(
        "localhost",
        help="documentation hosting address",
    ),
    port: int = typer.Option(
        8000,
        help="documentation hosting port",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        is_flag=True,
        help="Restart documentation at directory files changes",
    ),
) -> None:
    """Serve project AsyncAPI schema"""

    if ":" in app:
        module, app_obj = import_from_string(app)
        raw_schema = get_app_schema(app_obj)

        module_parent = module.parent
        extra_extensions: Sequence[str] = ()

    else:
        module_parent = Path.cwd()
        schema_filepath = module_parent / app
        extra_extensions = (schema_filepath.suffix,)

        if schema_filepath.suffix == ".json":
            data = schema_filepath.read_text()

        elif schema_filepath.suffix == ".yaml" or schema_filepath.suffix == ".yml":
            try:
                import yaml
            except ImportError as e:  # pragma: no cover
                typer.echo(INSTALL_YAML, err=True)
                raise typer.Exit(1) from e

            with schema_filepath.open("r") as f:
                schema = yaml.safe_load(f)

            data = json.dumps(schema)

        else:
            raise ValueError(
                f"Unknown extension given - {app}; Please provide app in format [python_module:FastStream] or [asyncapi.yaml/.json] - path to your application or documentation"
            )

        raw_schema = model_parse(Schema, data)

    if reload is True:
        try:
            from faststream.cli.supervisors.watchfiles import WatchReloader

        except ImportError:
            warnings.warn(INSTALL_WATCHFILES, category=ImportWarning, stacklevel=1)
            serve_app(raw_schema, host, port)

        else:
            WatchReloader(
                target=serve_app,
                args=(raw_schema, host, port),
                reload_dirs=(str(module_parent),),
                extra_extensions=extra_extensions,
            ).run()

    else:
        serve_app(raw_schema, host, port)


@docs_app.command(name="gen")
def gen(
    app: str = typer.Argument(
        ...,
        help="[python_module:FastStream] - path to your application",
    ),
    yaml: bool = typer.Option(
        False,
        "--yaml",
        is_flag=True,
        help="generate `asyncapi.yaml` schema",
    ),
    out: Optional[str] = typer.Option(
        None,
        help="output filename",
    ),
) -> None:
    """Generate project AsyncAPI schema"""
    _, app_obj = import_from_string(app)
    raw_schema = get_app_schema(app_obj)

    if yaml:
        try:
            schema = raw_schema.to_yaml()
        except ImportError as e:  # pragma: no cover
            typer.echo(INSTALL_YAML, err=True)
            raise typer.Exit(1) from e

        name = out or "asyncapi.yaml"

        with open(name, "w") as f:
            f.write(schema)

    else:
        schema = raw_schema.to_jsonable()
        name = out or "asyncapi.json"

        with open(name, "w") as f:
            json.dump(schema, f, indent=2)

    typer.echo(f"Your project AsyncAPI scheme was placed to `{name}`")
