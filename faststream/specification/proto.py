from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, Sequence, Union

from typing_extensions import Annotated, Doc

from faststream.specification.asyncapi.version import AsyncAPIVersion
from faststream.specification.schema.channel import Channel

if TYPE_CHECKING:
    from faststream.broker.core.usecase import BrokerUsecase
    from faststream.specification.schema.contact import Contact, ContactDict
    from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
    from faststream.specification.schema.license import License, LicenseDict
    from faststream.specification.schema.tag import Tag
    from faststream.types import (
        AnyDict,
        AnyHttpUrl,
    )


class Application(Protocol):
    broker: Optional["BrokerUsecase[Any, Any]"]

    title: str
    version: str
    description: str
    terms_of_service: Optional["AnyHttpUrl"]
    license: Optional[Union["License", "LicenseDict", "AnyDict"]]
    contact: Optional[Union["Contact", "ContactDict", "AnyDict"]]
    specs_tags: Optional[Sequence[Union["Tag", "AnyDict"]]]
    external_docs: Optional[Union["ExternalDocs", "ExternalDocsDict", "AnyDict"]]
    asyncapi_version: AsyncAPIVersion
    identifier: Optional[str]


class SpecificationProto(Protocol):
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
        Doc("Whatever to include operation in AsyncAPI schema or not."),
    ]

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
