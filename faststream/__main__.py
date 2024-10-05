"""CLI entry point to FastStream framework."""

import warnings

try:
    from faststream.cli.main import cli
except ImportError:
    has_typer = False
else:
    has_typer = True

if not has_typer:
    raise ImportError(
        "\n\nYou're trying to use the FastStream CLI, "
        "\nbut you haven't installed the required dependencies."
        "\nPlease install them using the following command: "
        '\npip install "faststream[cli]"'
    )

warnings.filterwarnings("default", category=ImportWarning, module="faststream")

if __name__ == "__main__":
    cli(prog_name="faststream")
