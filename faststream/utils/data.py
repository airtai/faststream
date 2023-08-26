from typing import Type, TypeVar

from faststream.types import AnyDict

TypedDictCls = TypeVar("TypedDictCls")


def filter_by_dict(typed_dict: Type[TypedDictCls], data: AnyDict) -> TypedDictCls:
    annotations = typed_dict.__annotations__
    return typed_dict(  # type: ignore
        {k: v for k, v in data.items() if k in annotations}
    )
