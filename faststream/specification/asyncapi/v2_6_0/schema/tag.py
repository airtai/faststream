from typing import Optional, Union, overload

import typing_extensions
from pydantic import BaseModel

from faststream._internal._compat import PYDANTIC_V2
from faststream._internal.basic_types import AnyDict
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.docs import (
    ExternalDocs,
)
from faststream.specification.asyncapi.v2_6_0.schema.docs import (
    from_spec as docs_from_spec,
)


class Tag(BaseModel):
    """A class to represent a tag.

    Attributes:
        name : name of the tag
        description : description of the tag (optional)
        externalDocs : external documentation for the tag (optional)

    """

    name: str
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocs] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"

    @classmethod
    def from_spec(cls, tag: spec.tag.Tag) -> typing_extensions.Self:
        return cls(
            name=tag.name,
            description=tag.description,
            externalDocs=docs_from_spec(tag.externalDocs) if tag.externalDocs else None,
        )


@overload
def from_spec(tag: spec.tag.Tag) -> Tag: ...


@overload
def from_spec(tag: spec.tag.TagDict) -> AnyDict: ...


@overload
def from_spec(tag: AnyDict) -> AnyDict: ...


def from_spec(
    tag: Union[spec.tag.Tag, spec.tag.TagDict, AnyDict],
) -> Union[Tag, AnyDict]:
    if isinstance(tag, spec.tag.Tag):
        return Tag.from_spec(tag)

    return dict(tag)
