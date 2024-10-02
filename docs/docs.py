"""A script to help with the translation of the docs."""

import os
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from shutil import rmtree
from typing import Optional

import mkdocs.commands.build
import mkdocs.commands.serve
import typer
from create_api_docs import create_api_docs
from expand_markdown import expand_markdown
from mkdocs.config import load_config
from typing_extensions import Annotated
from update_releases import find_metablock, update_release_notes

IGNORE_DIRS = ("assets", "stylesheets")

BASE_DIR = Path(__file__).resolve().parent
CONFIG = BASE_DIR / "mkdocs.yml"
DOCS_DIR = BASE_DIR / "docs"
LANGUAGES_DIRS = tuple(
    filter(lambda f: f.is_dir() and f.name not in IGNORE_DIRS, DOCS_DIR.iterdir()),
)
BUILD_DIR = BASE_DIR / "site"

EN_DOCS_DIR = DOCS_DIR / "en"
EN_INDEX_PATH = EN_DOCS_DIR / "index.md"
README_PATH = BASE_DIR.parent / "README.md"
EN_CONTRIBUTING_PATH = (
    EN_DOCS_DIR / "getting-started" / "contributing" / "CONTRIBUTING.md"
)
CONTRIBUTING_PATH = BASE_DIR.parent / "CONTRIBUTING.md"


config = load_config(str(CONFIG))

DEV_SERVER = str(config.get("dev_addr", "0.0.0.0:8008"))


def get_missing_translation(lng: str) -> Path:
    return DOCS_DIR / lng / "helpful" / "missing-translation.md"


def get_in_progress(lng: str) -> Path:
    return DOCS_DIR / lng / "helpful" / "in-progress.md"


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
    """A quick server to preview a built site with translations.

    For development, prefer the command live (or just mkdocs serve).
    This is here only to preview a built site.
    """
    _build()
    typer.echo("Warning: this is a very simple server.")
    typer.echo("For development, use the command live instead.")
    typer.echo("This is here only to preview a built site.")
    os.chdir(BUILD_DIR)
    addr, port = DEV_SERVER.split(":")
    server = HTTPServer((addr, int(port)), SimpleHTTPRequestHandler)
    typer.echo(f"Serving at: http://{DEV_SERVER}")
    server.serve_forever()


@app.command()
def live(port: Annotated[Optional[str], typer.Argument()] = None):
    dev_server = f"0.0.0.0:{port}" if port else DEV_SERVER

    typer.echo("Serving mkdocs with live reload")
    typer.echo(f"Serving at: http://{dev_server}")
    mkdocs.commands.serve.serve(dev_addr=dev_server)


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
                "{! " + get_in_progress(i.name) + " !}",
            )
            typer.echo(f"{file} - write `in progress`")

    if len(exists):
        for i in not_exists:
            file = i / path
            file.write_text(
                f"# {title or get_default_title(file)} \n"
                "{! " + get_missing_translation(i.name) + " !}",
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


@app.command()
def update_readme() -> None:
    """Update README.md by expanding embeddings in docs/docs/en/index.md."""
    # TODO: fix this function
    typer.echo("Skipping updating README.md for now")

    # typer.echo(f"Updating README.md")
    # expand_markdown(input_markdown_path=EN_INDEX_PATH, output_markdown_path=README_PATH)

    # remove_lines_between_dashes(file_path=README_PATH)

    # relative_path = os.path.relpath(EN_INDEX_PATH, BASE_DIR.parent)
    # auto_generated = f"[Note]: # (This is an auto-generated file. Please edit {relative_path} instead)\n\n"

    # existing_content = open(README_PATH).read()
    # open(README_PATH, "w").write(auto_generated + existing_content)


@app.command()
def update_contributing():
    """Update CONTRIBUTING.md by expanding embeddings in docs/docs/en/CONTRIBUTING.md."""
    typer.echo("Updating CONTRIBUTING.md")
    expand_markdown(
        input_markdown_path=EN_CONTRIBUTING_PATH,
        output_markdown_path=CONTRIBUTING_PATH,
    )

    existing_content = CONTRIBUTING_PATH.read_text()

    _, content = find_metablock(existing_content.splitlines())

    relative_path = EN_CONTRIBUTING_PATH.relative_to(BASE_DIR.parent)

    CONTRIBUTING_PATH.write_text(
        "\n".join(
            (
                f"> **_NOTE:_**  This is an auto-generated file. Please edit {relative_path} instead.",
                *content,
            ),
        )
        + "\n",
    )


@app.command()
def build_api_docs():
    """Build api docs for faststream."""
    typer.echo("Updating API docs")
    create_api_docs(root_path=BASE_DIR, module="faststream")


def _build():
    build_api_docs()
    update_readme()
    update_contributing()

    typer.echo("Updating Release Notes")
    update_release_notes(realease_notes_path=EN_DOCS_DIR / "release.md")

    subprocess.run(["mkdocs", "build", "--site-dir", BUILD_DIR], check=True)


if __name__ == "__main__":
    app()
