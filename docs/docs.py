import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from shutil import rmtree
import subprocess

from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import typer
import mkdocs.commands.build
import mkdocs.commands.serve


IGNORE_DIRS = ("assets",)

BASE_DIR = Path(__file__).resolve().parent
CONFIG = BASE_DIR / "mkdocs.yml"
DOCS_DIR = BASE_DIR / "docs"
LANGUAGES_DIRS = tuple(
    filter(lambda f: f.is_dir() and f.name not in IGNORE_DIRS, DOCS_DIR.iterdir())
)
BUILD_DIR = BASE_DIR / "site"

with CONFIG.open("r") as f:
    config = load(f, Loader)

DEV_SERVER = config.get("dev_addr", "0.0.0.0:8008")


def get_missing_translation(lng: str) -> str:
    return str(Path(DOCS_DIR.name) / lng / "helpful" / "missing-translation.md")


def get_in_progress(lng: str) -> str:
    return str(Path(DOCS_DIR.name) / lng / "helpful" / "in-progress.md")


app = typer.Typer()


def get_default_title(file: Path) -> str:
    title = file.stem.upper().replace("-", " ")
    if title == "INDEX":
        title = get_default_title(file.parent)
    return title


def join_nested(root: Path, path: str) -> Path:
    for i in path.split("/"):
        root = root / i
    return _touch_file(root)


def _touch_file(path: Path) -> Path:
    if not path.suffixes:
        path.mkdir(parents=True, exist_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


@app.command()
def preview():
    """
    A quick server to preview a built site with translations.
    For development, prefer the command live (or just mkdocs serve).
    This is here only to preview a builded site.
    """
    _build()
    typer.echo("Warning: this is a very simple server.")
    typer.echo("For development, use the command live instead.")
    typer.echo("This is here only to preview a builded site.")
    os.chdir(str(BUILD_DIR))
    addr, port = DEV_SERVER.split(":")
    server = HTTPServer((addr, int(port)), SimpleHTTPRequestHandler)
    typer.echo(f"Serving at: http://{DEV_SERVER}")
    server.serve_forever()


@app.command()
def live():
    typer.echo("Serving mkdocs with live reload")
    typer.echo(f"Serving at: http://{DEV_SERVER}")
    mkdocs.commands.serve.serve(dev_addr=DEV_SERVER)


@app.command()
def build():
    _build()


@app.command()
def add(path=typer.Argument(...)):
    title = ""

    exists = []
    not_exists = []

    for i in LANGUAGES_DIRS:
        file = join_nested(i, path)

        if file.exists():
            exists.append(i)

            if not title:
                with file.open("r") as r:
                    title = r.readline()

        else:
            not_exists.append(i)
            file.write_text(
                f"# {title or get_default_title(file)} \n"
                "{! " + get_in_progress(i.name) + " !}"
            )
            typer.echo(f"{file} - write `in progress`")

    if len(exists):
        for i in not_exists:
            file = i / path
            file.write_text(
                f"# {title or get_default_title(file)} \n"
                "{! " + get_missing_translation(i.name) + " !}"
            )
            typer.echo(f"{file} - write `missing translation`")


@app.command()
def rm(path: str = typer.Argument(...)):
    delete = typer.confirm("Are you sure you want to delete files?")
    if not delete:
        typer.echo("Not deleting")
        raise typer.Abort()

    for i in LANGUAGES_DIRS:
        file = i / path
        if file.exists():
            if file.is_dir():
                rmtree(file)
            else:
                file.unlink()
            typer.echo(f"{file} removed")

        if file.parent.exists() and not tuple(file.parent.iterdir()):
            file.parent.rmdir()
            typer.echo(f"{file.parent} removed")


@app.command()
def mv(path: str = typer.Argument(...), new_path: str = typer.Argument(...)):
    for i in LANGUAGES_DIRS:
        file = i / path
        if file.exists():
            file.rename(i / new_path)
            typer.echo(f"{i / new_path} moved")


def _build():
    subprocess.run(["mkdocs", "build", "--site-dir", BUILD_DIR], check=True)


if __name__ == "__main__":
    app()
