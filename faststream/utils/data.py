from typing import Type, TypeVar

from faststream.types import AnyDict

TypedDictCls = TypeVar("TypedDictCls")


def filter_by_dict(typed_dict: Type[TypedDictCls], data: AnyDict) -> TypedDictCls:
    """Filter a dictionary based on a typed dictionary.

    Args:
        typed_dict: The typed dictionary to filter by.
        data: The dictionary to filter.

    Returns:
        A new instance of the typed dictionary with only the keys present in the data dictionary.
    """
    annotations = typed_dict.__annotations__
    return typed_dict(  # type: ignore
        {k: v for k, v in data.items() if k in annotations}
    )
