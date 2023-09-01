import contextlib
import os
from pathlib import Path
from typing import Generator


@contextlib.contextmanager
def working_directory(path: str) -> Generator[None, None, None]:
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)
