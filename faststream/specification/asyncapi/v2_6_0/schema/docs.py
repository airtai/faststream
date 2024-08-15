from typing import Any, Dict, Optional, Union, overload

import typing_extensions
from pydantic import AnyHttpUrl, BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.specification import schema as spec


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

    @classmethod
    def from_spec(cls, docs: spec.docs.ExternalDocs) -> typing_extensions.Self:
        return cls(
            url=docs.url,
            description=docs.description
        )


@overload
def from_spec(docs: spec.docs.ExternalDocs) -> ExternalDocs: ...


@overload
def from_spec(docs: spec.docs.ExternalDocsDict) -> Dict[str, Any]: ...


@overload
def from_spec(docs: Dict[str, Any]) -> Dict[str, Any]: ...


def from_spec(
        docs: Union[spec.docs.ExternalDocs, spec.docs.ExternalDocsDict, Dict[str, Any]]
) -> Union[ExternalDocs, Dict[str, Any]]:
    if isinstance(docs, spec.docs.ExternalDocs):
        return ExternalDocs.from_spec(docs)

    return dict(docs)
