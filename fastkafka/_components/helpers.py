# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/998_Internal_Helpers.ipynb.

# %% auto 0
__all__ = ['in_notebook', 'change_dir', 'ImportFromStringError', 'true_after', 'unwrap_list_type']

# %% ../../nbs/998_Internal_Helpers.ipynb 2
def in_notebook() -> bool:
    try:
        from IPython import get_ipython

        if "IPKernelApp" not in get_ipython().config:
            return False
    except ImportError:
        return False
    except AttributeError:
        return False
    return True

# %% ../../nbs/998_Internal_Helpers.ipynb 4
import contextlib
import importlib
import os
import sys
from datetime import datetime, timedelta
from functools import wraps
from inspect import signature, Parameter
from pathlib import Path
from typing import *

import docstring_parser
import typer

from .meta import delegates

# %% ../../nbs/998_Internal_Helpers.ipynb 6
@contextlib.contextmanager
def change_dir(d: str) -> Generator[None, None, None]:
    curdir = os.getcwd()
    os.chdir(d)
    try:
        yield
    finally:
        os.chdir(curdir)

# %% ../../nbs/998_Internal_Helpers.ipynb 8
class ImportFromStringError(Exception):
    pass


def _import_from_string(import_str: str) -> Any:
    """Imports library from string

    Note:
        copied from https://github.com/encode/uvicorn/blob/master/uvicorn/importer.py

    Args:
        import_str: input string in form 'main:app'

    """
    sys.path.append(".")

    if not isinstance(import_str, str):
        return import_str

    module_str, _, attrs_str = import_str.partition(":")
    if not module_str or not attrs_str:
        message = (
            'Import string "{import_str}" must be in format "<module>:<attribute>".'
        )
        typer.secho(f"{message}", err=True, fg=typer.colors.RED)
        raise ImportFromStringError(message.format(import_str=import_str))

    try:
        # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
        module = importlib.import_module(module_str)
    except ImportError as exc:
        if exc.name != module_str:
            raise exc from None
        message = 'Could not import module "{module_str}".'
        raise ImportFromStringError(message.format(module_str=module_str))

    instance = module
    try:
        for attr_str in attrs_str.split("."):
            instance = getattr(instance, attr_str)
    except AttributeError:
        message = 'Attribute "{attrs_str}" not found in module "{module_str}".'
        raise ImportFromStringError(
            message.format(attrs_str=attrs_str, module_str=module_str)
        )

    return instance

# %% ../../nbs/998_Internal_Helpers.ipynb 10
def true_after(seconds: Union[int, float]) -> Callable[[], bool]:
    """Function returning True after a given number of seconds"""
    t = datetime.now()

    def _true_after(seconds: Union[int, float] = seconds, t: datetime = t) -> bool:
        return (datetime.now() - t) > timedelta(seconds=seconds)

    return _true_after

# %% ../../nbs/998_Internal_Helpers.ipynb 12
def unwrap_list_type(var_type: Union[Type, Parameter]) -> Union[Type, Parameter]:
    """
    Unwraps the type of a list.

    Vars:
        var_type: Type to unwrap.

    Returns:
        Unwrapped type if the given type is a list, otherwise returns the same type.

    Example:
        - Input: List[str]
          Output: str
        - Input: int
          Output: int
    """
    if hasattr(var_type, "__origin__") and var_type.__origin__ == list:
        return var_type.__args__[0]  # type: ignore
    else:
        return var_type
