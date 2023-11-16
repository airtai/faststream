import importlib
from types import ModuleType
from typing import Tuple

import typer

from faststream.app import FastStream


def import_from_string(import_str: str) -> Tuple[ModuleType, FastStream]:
    """
    Import FastStream application from module specified by a string.

    Parameters:
        import_str (str): A string in the format "<module>:<attribute>" specifying the module and faststream application to import.

    Returns:
        Tuple[ModuleType, FastStream]: A tuple containing the imported module and the faststream application.

    Raises:
        typer.BadParameter: Raised if the given value is not of type string, if the import string is not in the format
            "<module>:<attribute>", if the module is not found, or if the faststream appliation is not found in the module.
    """
    if not isinstance(import_str, str):
        raise typer.BadParameter("Given value is not of type string")

    module_str, _, attrs_str = import_str.partition(":")
    if not module_str or not attrs_str:
        raise typer.BadParameter(
            f'Import string "{import_str}" must be in format "<module>:<attribute>"'
        )

    try:
        module = importlib.import_module(  # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
            module_str
        )
    except ModuleNotFoundError as e:
        typer.echo(e, err=True)
        raise typer.BadParameter(
            "Please, input module like '<module>:<attribute>'"
        ) from e

    instance = module
    try:
        for attr_str in attrs_str.split("."):
            instance = getattr(instance, attr_str)
    except AttributeError as e:
        typer.echo(e, err=True)
        raise typer.BadParameter(
            f'Attribute "{attrs_str}" not found in module "{module_str}".'
        ) from e

    return module, instance  # type: ignore[return-value]
