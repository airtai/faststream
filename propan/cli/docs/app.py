import json
import sys
from pathlib import Path
from typing import Optional, Union

import typer

from propan._compat import model_parse
from propan.asyncapi.generate import get_app_schema
from propan.asyncapi.schema import Schema
from propan.asyncapi.site import serve_app
from propan.cli.utils.imports import get_app_path, try_import_propan
from propan.types import AnyDict

docs_app = typer.Typer(pretty_exceptions_short=True)


@docs_app.command(name="serve")
def serve(
    app: str = typer.Argument(
        ...,
        help="[python_module:PropanApp] or [asyncapi.yaml/.json] - path to your application or documentation",
    ),
    host: str = typer.Option(
        "localhost",
        help="documentation hosting address",
    ),
    port: int = typer.Option(
        8000,
        help="documentation hosting port",
    ),
) -> None:
    """Serve project AsyncAPI schema"""
    if ":" in app:
        module, app = get_app_path(app)
        sys.path.insert(0, str(module.parent))
        propan_app = try_import_propan(module, app)
        raw_schema = get_app_schema(propan_app)

    else:
        schema_filepath = Path.cwd() / app
        raw_schema = model_parse(Schema, schema_filepath.read_text())

    serve_app(
        schema=raw_schema,
        host=host,
        port=port,
    )


@docs_app.command(name="gen")
def gen(
    app: str = typer.Argument(
        ...,
        help="[python_module:PropanApp] - path to your application",
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
    if ":" in app:
        module, app = get_app_path(app)
        sys.path.insert(0, str(module.parent))
        propan_app = try_import_propan(module, app)
        raw_schema = get_app_schema(propan_app)

    else:
        schema_filepath = Path.cwd() / app
        raw_schema = model_parse(Schema, schema_filepath.read_text())

    schema: Union[str, AnyDict]
    if yaml:
        name = out or "asyncapi.yaml"
        schema = ""

    else:
        name = out or "asyncapi.json"
        schema = raw_schema.to_jsonable()

        with open(name, "w") as f:
            json.dump(schema, f, indent=2)
