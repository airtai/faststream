from typing import Optional, Union

from pydantic import AnyHttpUrl, BaseModel, Field
from typing_extensions import Required, TypedDict

from faststream._compat import PYDANTIC_V2


class ExternalDocsDict(TypedDict, total=False):
    """A dictionary type for representing external documentation.

    Attributes:
        url : Required URL for the external documentation
        description : Description of the external documentation

    """

    url: Required[AnyHttpUrl]
    description: str


class ExternalDocs(BaseModel):
    """A class to represent external documentation.

    Attributes:
        url : URL of the external documentation
        description : optional description of the external documentation

    """

    url: AnyHttpUrl
    description: Optional[str] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class TagDict(TypedDict, total=False):
    """A dictionary-like class for storing tags.

    Attributes:
        name : required name of the tag
        description : description of the tag
        externalDocs : external documentation for the tag

    """

    name: Required[str]
    description: str
    externalDocs: Union[ExternalDocs, ExternalDocsDict]


class Tag(BaseModel):
    """A class to represent a tag.

    Attributes:
        name : name of the tag
        description : description of the tag (optional)
        externalDocs : external documentation for the tag (optional)

    """

    name: str
    description: Optional[str] = None
    externalDocs: Optional[Union[ExternalDocs, ExternalDocsDict]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class Reference(BaseModel):
    """A class to represent a reference.

    Attributes:
        ref : the reference string

    """

    ref: str = Field(..., alias="$ref")


class Parameter(BaseModel):
    """A class to represent a parameter."""

    # TODO
    ...
