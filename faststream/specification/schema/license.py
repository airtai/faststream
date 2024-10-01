from typing import (
    Optional,
)

from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import Required, TypedDict

from faststream._internal._compat import (
    PYDANTIC_V2,
)


class LicenseDict(TypedDict, total=False):
    """A dictionary-like class to represent a license.

    Attributes:
        name : required name of the license (type: str)
        url : URL of the license (type: AnyHttpUrl)
    """

    name: Required[str]
    url: AnyHttpUrl


class License(BaseModel):
    """A class to represent a license.

    Attributes:
        name : name of the license
        url : URL of the license (optional)

    Config:
        extra : allow additional attributes in the model (PYDANTIC_V2)
    """

    name: str
    url: Optional[AnyHttpUrl] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
