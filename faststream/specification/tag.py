from dataclasses import dataclass
from typing import Optional, Union

from typing_extensions import Required, TypedDict

from faststream.specification.docs import ExternalDocs, ExternalDocsDict


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


@dataclass
class Tag:
    """A class to represent a tag.

    Attributes:
        name : name of the tag
        description : description of the tag (optional)
        externalDocs : external documentation for the tag (optional)

    """

    name: str
    description: Optional[str] = None
    externalDocs: Optional[Union[ExternalDocs, ExternalDocsDict]] = None
