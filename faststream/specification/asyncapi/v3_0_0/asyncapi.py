from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from faststream._internal.broker.broker import BrokerUsecase
from faststream.specification.asyncapi.base.asyncapi import AsyncAPIProto
from faststream.specification.asyncapi.v3_0_0.generate import get_app_schema

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, AnyHttpUrl
    from faststream.specification.schema.contact import Contact, ContactDict
    from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
    from faststream.specification.schema.license import License, LicenseDict
    from faststream.specification.schema.tag import Tag, TagDict


class AsyncAPI3(AsyncAPIProto):
    def __init__(
            self,
            broker: BrokerUsecase[Any, Any],
            /,
            title: str = "FastStream",
            app_version: str = "0.1.0",
            schema_version: str = "2.6.0",
            description: str = "",
            terms_of_service: Optional["AnyHttpUrl"] = None,
            contact: Optional[Union["Contact", "ContactDict", "AnyDict"]] = None,
            license: Optional[Union["License", "LicenseDict", "AnyDict"]] = None,
            identifier: Optional[str] = None,
            tags: Optional[Sequence[Union["Tag", "TagDict", "AnyDict"]]] = None,
            external_docs: Optional[Union["ExternalDocs", "ExternalDocsDict", "AnyDict"]] = None,
    ) -> None:
        self.broker = broker
        self.title = title
        self.app_version = app_version
        self.schema_version = schema_version
        self.description = description
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license = license
        self.identifier = identifier
        self.tags = tags
        self.external_docs = external_docs

    def json(self) -> str:
        return get_app_schema(
            self.broker,
            title=self.title,
            app_version=self.app_version,
            schema_version=self.schema_version,
            description=self.description,
            terms_of_service=self.terms_of_service,
            contact=self.contact,
            license=self.license,
            identifier=self.identifier,
            tags=self.tags,
            external_docs=self.external_docs,
        ).to_json()

    def jsonable(self) -> Any:
        return get_app_schema(
            self.broker,
            title=self.title,
            app_version=self.app_version,
            schema_version=self.schema_version,
            description=self.description,
            terms_of_service=self.terms_of_service,
            contact=self.contact,
            license=self.license,
            identifier=self.identifier,
            tags=self.tags,
            external_docs=self.external_docs,
        ).to_jsonable()

    def yaml(self) -> str:
        return get_app_schema(
            self.broker,
            title=self.title,
            app_version=self.app_version,
            schema_version=self.schema_version,
            description=self.description,
            terms_of_service=self.terms_of_service,
            contact=self.contact,
            license=self.license,
            identifier=self.identifier,
            tags=self.tags,
            external_docs=self.external_docs,
        ).to_yaml()
