import importlib
from types import ModuleType
from typing import Tuple

from faststream.app import FastStream


class ImportFromStringError(Exception):
    pass


def import_from_string(import_str: str) -> Tuple[ModuleType, FastStream]:
    if not isinstance(import_str, str):
        raise ImportFromStringError("Given value is not of type string")

    module_str, _, attrs_str = import_str.partition(":")
    if not module_str or not attrs_str:
        raise ImportFromStringError(
            f'Import string "{import_str}" must be in format "<module>:<attribute>".'
        )

    try:
        module = importlib.import_module(  # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
            module_str
        )
    except ModuleNotFoundError as e:
        if e.name != module_str:
            raise e from None
        raise ImportFromStringError(f'Could not import module "{module_str}".') from e

    instance = module
    try:
        for attr_str in attrs_str.split("."):
            instance = getattr(instance, attr_str)
    except AttributeError as e:
        raise ImportFromStringError(
            f'Attribute "{attrs_str}" not found in module "{module_str}".'
        ) from e

    return module, instance  # type: ignore[return-value]
