import os
import contextlib
from pathlib import Path
from typing import ContextManager

@contextlib.contextmanager
def working_directory(path: str) -> ContextManager[None]:
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)