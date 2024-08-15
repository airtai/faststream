from dataclasses import asdict
from typing import Any, Dict, Optional, Union, overload

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.docs import (
    ExternalDocs,
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


@overload
def from_spec(tag: spec.tag.Tag) -> Tag: ...


@overload
def from_spec(tag: spec.tag.TagDict) -> Dict[str, Any]: ...


@overload
def from_spec(tag: Dict[str, Any]) -> Dict[str, Any]: ...


def from_spec(
        tag: Union[spec.tag.Tag, spec.tag.TagDict, Dict[str, Any]]
) -> Union[Tag, Dict[str, Any]]:
    if isinstance(tag, spec.tag.Tag):
        return Tag(**asdict(tag))

    return dict(tag)
