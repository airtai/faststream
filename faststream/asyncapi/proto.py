from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, Sequence, Union

from typing_extensions import Annotated, Doc

from faststream.asyncapi.version import AsyncAPIVersion
from faststream.specification.contact import Contact, ContactDict
from faststream.specification.license import License, LicenseDict

if TYPE_CHECKING:
    from faststream.broker.core.usecase import BrokerUsecase
    from faststream.specification.channel import Channel
    from faststream.specification.docs import ExternalDocs, ExternalDocsDict
    from faststream.specification.tag import Tag, TagDict
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
    asyncapi_version: AsyncAPIVersion
    identifier: Optional[str]


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
        Doc("Whatever to include operation in AsyncAPI schema or not."),
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
