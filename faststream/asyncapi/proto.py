from abc import abstractmethod
from typing import TYPE_CHECKING, Dict, Optional, Protocol

from typing_extensions import Annotated, Doc

if TYPE_CHECKING:
    from faststream.asyncapi.schema.channels import Channel


class AsyncAPIProto(Protocol):
    """A class representing an asynchronous API operation."""

    title_: Annotated[
        Optional[str],
        Doc("AsyncAPI object title."),
    ]
    description_: Annotated[
        Optional[str],
        Doc("AsyncAPI object description."),
    ]
    include_in_schema: Annotated[
        bool,
        Doc("Whetever to include operation in AsyncAPI schema or not."),
    ]

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the API operation."""
        ...

    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """Returns the description of the API operation."""
        ...

    @abstractmethod
    def schema(self) -> Dict[str, "Channel"]:
        """Generate AsyncAPI schema."""
        ...
