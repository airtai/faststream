from abc import abstractmethod
from typing import Dict, Optional

from typing_extensions import Annotated, Doc

from faststream.asyncapi.schema.channels import Channel


class AsyncAPIOperation:
    """A class representing an asynchronous API operation."""

    def __init__(
        self,
        *,
        title_: Annotated[
            Optional[str],
            Doc("AsyncAPI object title."),
        ],
        description_: Annotated[
            Optional[str],
            Doc("AsyncAPI object description."),
        ],
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ],
    ) -> None:
        """Initialize AsyncAPI operation object."""
        self.title_ = title_
        self.description_ = description_
        self.include_in_schema = include_in_schema

    @property
    def name(self) -> str:
        """Returns the name of the API operation."""
        return self.title_ or self.get_name()

    @abstractmethod
    def get_name(self) -> str:
        """Name property fallback."""
        raise NotImplementedError()

    @property
    def description(self) -> Optional[str]:
        """Returns the description of the API operation."""
        return self.description_ or self.get_description()

    def get_description(self) -> Optional[str]:
        """Description property fallback."""
        return None

    def schema(self) -> Dict[str, Channel]:
        """Returns the schema of the API operation as a dictionary of channel names and channel objects."""
        if self.include_in_schema:
            return self.get_schema()
        else:
            return {}

    @abstractmethod
    def get_schema(self) -> Dict[str, Channel]:
        """Generate AsyncAPI schema."""
        raise NotImplementedError()
