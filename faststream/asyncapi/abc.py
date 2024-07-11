from abc import abstractmethod
from typing import Any, Dict, Optional

from faststream.asyncapi.proto import AsyncAPIProto
from faststream.asyncapi.schema.channels import Channel


class AsyncAPIOperation(AsyncAPIProto):
    """A class representing an asynchronous API operation."""

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

    @abstractmethod
    def get_payloads(self) -> Any:
        """Generate AsyncAPI payloads."""
        raise NotImplementedError()
