from typing import Optional, Union, cast, overload

from pydantic import BaseModel
from typing_extensions import Self

from faststream._internal._compat import PYDANTIC_V2
from faststream._internal.basic_types import AnyDict
from faststream._internal.utils.data import filter_by_dict
from faststream.specification.asyncapi.v2_6_0.schema.docs import ExternalDocs
from faststream.specification.schema.extra import (
    Tag as SpecTag,
    TagDict,
)


class Tag(BaseModel):
    """A class to represent a tag.

    Attributes:
        name : name of the tag
        description : description of the tag (optional)
        externalDocs : external documentation for the tag (optional)
    """

    name: str
    # Use default values to be able build from dict
    description: Optional[str] = None
    externalDocs: Optional[ExternalDocs] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"

    @overload
    @classmethod
    def from_spec(cls, tag: SpecTag) -> Self: ...

    @overload
    @classmethod
    def from_spec(cls, tag: TagDict) -> Self: ...

    @overload
    @classmethod
    def from_spec(cls, tag: AnyDict) -> AnyDict: ...

    @classmethod
    def from_spec(cls, tag: Union[SpecTag, TagDict, AnyDict]) -> Union[Self, AnyDict]:
        if isinstance(tag, SpecTag):
            return cls(
                name=tag.name,
                description=tag.description,
                externalDocs=ExternalDocs.from_spec(tag.external_docs),
            )

        tag = cast("AnyDict", tag)
        tag_data, custom_data = filter_by_dict(TagDict, tag)

        if custom_data:
            return tag

        return cls(
            name=tag_data.get("name"),
            description=tag_data.get("description"),
            externalDocs=tag_data.get("external_docs"),
        )
