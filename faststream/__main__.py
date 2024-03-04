"""CLI entry point to FastStream library."""

import warnings

from faststream.cli.main import cli

warnings.filterwarnings("default", category=ImportWarning, module="faststream")

if __name__ == "__main__":
    cli(prog_name="faststream")
