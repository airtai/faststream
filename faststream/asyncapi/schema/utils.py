from typing import Optional, Union

from pydantic import AnyHttpUrl, BaseModel, Field

from faststream._compat import PYDANTIC_V2, Required, TypedDict


class ExternalDocsDict(TypedDict, total=False):
    url: Required[AnyHttpUrl]
    description: str


class ExternalDocs(BaseModel):
    url: AnyHttpUrl
    description: Optional[str] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class TagDict(TypedDict, total=False):
    name: Required[str]
    description: str
    externalDocs: Union[ExternalDocs, ExternalDocsDict]


class Tag(BaseModel):
    name: str
    description: Optional[str] = None
    externalDocs: Optional[Union[ExternalDocs, ExternalDocsDict]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class Reference(BaseModel):
    ref: str = Field(..., alias="$ref")


class Parameter(BaseModel):
    # TODO
    ...
