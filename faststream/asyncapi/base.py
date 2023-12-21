from abc import abstractproperty
from dataclasses import dataclass, field
from typing import Dict

from faststream.asyncapi.schema.channels import Channel


@dataclass
class AsyncAPIOperation:
    """A class representing an asynchronous API operation.

    Attributes:
        name : name of the API operation

    Methods:
        schema() : returns the schema of the API operation as a dictionary of channel names and channel objects

    """

    include_in_schema: bool = field(default=True)

    @abstractproperty
    def name(self) -> str:
        """Returns the name of the API operation."""
        raise NotImplementedError()

    def schema(self) -> Dict[str, Channel]:  # pragma: no cover
        """Returns the schema of the API operation as a dictionary of channel names and channel objects."""
        return {}
