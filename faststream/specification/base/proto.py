from abc import abstractmethod
from typing import Any, Optional, Protocol

from faststream.specification.schema.channel import Channel


class EndpointProto(Protocol):
    """A class representing an asynchronous API operation."""

    title_: Optional[str]
    description_: Optional[str]
    include_in_schema: bool

    @property
    def name(self) -> str:
        """Returns the name of the API operation."""
        return self.title_ or self.get_name()

    @abstractmethod
    def get_name(self) -> str:
        """Name property fallback."""
        raise NotImplementedError

    @property
    def description(self) -> Optional[str]:
        """Returns the description of the API operation."""
        return self.description_ or self.get_description()

    def get_description(self) -> Optional[str]:
        """Description property fallback."""
        return None

    def schema(self) -> dict[str, Channel]:
        """Returns the schema of the API operation as a dictionary of channel names and channel objects."""
        if self.include_in_schema:
            return self.get_schema()
        return {}

    @abstractmethod
    def get_schema(self) -> dict[str, Channel]:
        """Generate AsyncAPI schema."""
        raise NotImplementedError

    @abstractmethod
    def get_payloads(self) -> Any:
        """Generate AsyncAPI payloads."""
        raise NotImplementedError
