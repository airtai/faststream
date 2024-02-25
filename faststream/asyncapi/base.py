from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional

from faststream.asyncapi.schema.channels import Channel


@dataclass
class AsyncAPIOperation:
    """A class representing an asynchronous API operation.

    Attributes:
        name : name of the API operation

    Methods:
        schema() : returns the schema of the API operation as a dictionary of channel names and channel objects

    """

    title_: Optional[str]
    description_: Optional[str]
    include_in_schema: bool

    @property
    def name(self) -> str:
        """Returns the name of the API operation."""
        return self.title_ or self.get_name()

    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError()

    @property
    def description(self) -> Optional[str]:
        """Returns the description of the API operation."""
        return self.description_ or self.get_description()

    def get_description(self) -> Optional[str]:
        return None

    def schema(self) -> Dict[str, Channel]:
        """Returns the schema of the API operation as a dictionary of channel names and channel objects."""
        if self.include_in_schema:
            return self.get_schema()
        else:
            return {}

    @abstractmethod
    def get_schema(self) -> Dict[str, Channel]:
        raise NotImplementedError()
