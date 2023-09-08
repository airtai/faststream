import os
from inspect import getsourcefile
from pathlib import Path
from types import FunctionType
from typing import Any, Tuple, Type, Union

import griffe
from mkdocs.config import load_config


def _add_mkdocstring_header_config(
    autodoc: str, heading_level: int, show_category_heading: bool, is_root_object: bool
) -> str:
    """Adds the mkdocstring header configuration to the autodoc string.

    Args:
        autodoc: The autodoc string to modify.
        heading_level: The base heading level set in the mkdocs config file.
        show_category_heading: The value of the show_category_heading flag set in the mkdocs config file.
        is_root_object: A flag indicating whether the object is the root object.

    Returns:
        The modified autodoc string with the heading level and options.

    """
    if not is_root_object:
        autodoc_header_level = (
            heading_level + 2 if show_category_heading else heading_level + 1
        )
        autodoc += f"    options:\n      heading_level: {autodoc_header_level}\n      show_root_full_path: false\n"
    return autodoc


def _get_symbol_filepath(symbol: Union[FunctionType, Type[Any]]) -> Path:
    lib_name = "faststream"
    filepath = getsourcefile(symbol)
    return Path(filepath).relative_to(  # type: ignore
        filepath.split(f"{lib_name}/")[0]  # type: ignore
    )


def _generate_autodoc(symbol: Union[FunctionType, Type[Any]], symbol_path: Path) -> str:
    return f"\n\n::: {os.path.splitext(str(symbol_path).replace('/', '.'))[0]}.{symbol.__name__}\n"


def _generate_autodoc_string(
    symbol: Union[FunctionType, Type[Any]],
    *,
    heading_level: int,
    show_category_heading: bool,
    is_root_object: bool = True,
) -> str:
    """Generate the autodoc string for the given symbol.

    Args:
        symbol: The symbol to generate the autodoc string for.
        heading_level: The base heading level set in the mkdocs config file.
        show_category_heading: The value of the show_category_heading flag set in the mkdocs config file.
        is_root_object: A flag indicating whether the object is the root object.

    Returns:
        The generated autodoc string with the appropriate heading level and options.

    """
    try:
        module = f"{symbol.__module__}.{symbol.__qualname__}"
        parsed_module = griffe.load(module)
        if "raise NotImplementedError()" in parsed_module.source:
            raise KeyError
        autodoc = f"\n\n::: {module}\n"
    except KeyError as e:
        patched_symbol_path = _get_symbol_filepath(symbol)
        autodoc = _generate_autodoc(symbol, patched_symbol_path)

    return _add_mkdocstring_header_config(
        autodoc, heading_level, show_category_heading, is_root_object
    )


def _get_mkdocstring_config(mkdocs_path: Path) -> Tuple[int, bool]:
    """Get the mkdocstring configuration from the mkdocs.yml file.

    Args:
        mkdocs_path: The path to the mkdocs directory.

    Returns:
        A tuple containing the heading level and show category heading settings.

    Raises:
        RuntimeError: If the mkdocstrings settings cannot be read from the mkdocs.yml file.

    """
    config = load_config(str(mkdocs_path / "mkdocs.yml"))
    mkdocstrings_config = config["plugins"]["mkdocstrings"].config

    mkdocstrings_options = mkdocstrings_config["handlers"][
        "python"
    ]["options"]
    heading_level = mkdocstrings_options.get("heading_level", 2)
    show_category_heading = mkdocstrings_options.get("show_category_heading", False)

    return heading_level, show_category_heading


def get_formatted_docstring_for_symbol(
    symbol: Union[FunctionType, Type[Any]], mkdocs_path: Path
) -> str:
    """Recursively parses and get formatted docstring of a symbol.

    Args:
        symbol: A Python class or function object to parse the docstring for.
        mkdocs_path: The path to the mkdocs folder.

    Returns:
        A formatted docstring of the symbol and its members.

    """
    # if symbol.__doc__ is None:
    #     return ""

    heading_level, show_category_heading = _get_mkdocstring_config(mkdocs_path)
    contents = _generate_autodoc_string(
        symbol, heading_level=heading_level, show_category_heading=show_category_heading
    )
    return contents
