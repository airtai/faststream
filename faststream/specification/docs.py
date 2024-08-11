from dataclasses import dataclass
from typing import Optional

from typing_extensions import Required, TypedDict


class ExternalDocsDict(TypedDict, total=False):
    """A dictionary type for representing external documentation.

    Attributes:
        url : Required URL for the external documentation
        description : Description of the external documentation

    """

    url: Required[str]
    description: str


@dataclass
class ExternalDocs:
    """A class to represent external documentation.

    Attributes:
        url : URL of the external documentation
        description : optional description of the external documentation

    """

    url: str
    description: Optional[str] = None
