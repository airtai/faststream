import typer

from .asyncapi import asyncapi_app

docs_app = typer.Typer(pretty_exceptions_short=True)
docs_app.add_typer(asyncapi_app, name="asyncapi")
