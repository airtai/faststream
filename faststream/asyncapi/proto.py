from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, Sequence, Union

if TYPE_CHECKING:
    from faststream.asyncapi.schema import (
        Contact,
        ContactDict,
        ExternalDocs,
        ExternalDocsDict,
        License,
        LicenseDict,
        Tag,
        TagDict,
    )
    from faststream.asyncapi.schema.channels import Channel
    from faststream.broker.core.usecase import BrokerUsecase
    from faststream.types import (
        AnyDict,
        AnyHttpUrl,
    )


class AsyncAPIApplication(Protocol):
    broker: Optional["BrokerUsecase[Any, Any]"]

    title: str
    version: str
    description: str
    terms_of_service: Optional["AnyHttpUrl"]
    license: Optional[Union["License", "LicenseDict", "AnyDict"]]
    contact: Optional[Union["Contact", "ContactDict", "AnyDict"]]
    asyncapi_tags: Optional[Sequence[Union["Tag", "TagDict", "AnyDict"]]]
    external_docs: Optional[Union["ExternalDocs", "ExternalDocsDict", "AnyDict"]]
    identifier: Optional[str]


class AsyncAPIProto(Protocol):
    """A class representing an asynchronous API operation."""

    title_: Optional[str]
    """AsyncAPI object title."""

    description_: Optional[str]
    """AsyncAPI object description."""

    include_in_schema: bool
    """Whetever to include operation in AsyncAPI schema or not."""

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
