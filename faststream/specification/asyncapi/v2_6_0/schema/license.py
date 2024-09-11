from typing import (
    Optional,
    Union,
    overload,
)

from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import Self

from faststream._compat import (
    PYDANTIC_V2,
)
from faststream.specification import schema as spec
from faststream.types import AnyDict


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

    @classmethod
    def from_spec(cls, license: spec.license.License) -> Self:
        return cls(
            name=license.name,
            url=license.url,
        )


@overload
def from_spec(license: spec.license.License) -> License: ...


@overload
def from_spec(license: spec.license.LicenseDict) -> AnyDict: ...


@overload
def from_spec(license: AnyDict) -> AnyDict: ...


def from_spec(
    license: Union[spec.license.License, spec.license.LicenseDict, AnyDict],
) -> Union[License, AnyDict]:
    if isinstance(license, spec.license.License):
        return License.from_spec(license)

    return dict(license)
