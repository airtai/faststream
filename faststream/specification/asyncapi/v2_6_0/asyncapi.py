from typing import Any, Optional, Union, Sequence

from faststream._internal.basic_types import AnyHttpUrl, AnyDict
from faststream._internal.broker.broker import BrokerUsecase
from faststream.specification.asyncapi.base.asyncapiproto import AsyncAPIProto
from faststream.specification.asyncapi.v2_6_0 import get_app_schema
from faststream.specification.schema.contact import Contact, ContactDict
from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
from faststream.specification.schema.license import LicenseDict, License
from faststream.specification.schema.tag import Tag, TagDict


class AsyncAPI2(AsyncAPIProto):
    def __init__(
            self,
            broker: BrokerUsecase[Any, Any],
            /,
            title: str = "FastStream",
            version: str = "0.1.0",
            schema_version: str = "2.6.0",
            description: str = "",
            terms_of_service: Optional["AnyHttpUrl"] = None,
            contact: Optional[Union["Contact", "ContactDict", "AnyDict"]] = None,
            license: Optional[Union["License", "LicenseDict", "AnyDict"]] = None,
            identifier: Optional[str] = None,
            specs_tags: Optional[Sequence[Union["Tag", "TagDict", "AnyDict"]]] = None,
            external_docs: Optional[Union["ExternalDocs", "ExternalDocsDict", "AnyDict"]] = None,
    ) -> None:
        self.broker = broker
        self.title = title
        self.version = version
        self.schema_version = schema_version
        self.description = description
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license = license
        self.identifier = identifier
        self.specs_tags = specs_tags
        self.external_docs = external_docs

    def json(self) -> str:
        return get_app_schema(
            self.broker,
            title=self.title,
            app_version=self.version,
            schema_version=self.schema_version,
            description=self.description,
            terms_of_service=self.terms_of_service,
            contact=self.contact,
            license=self.license,
            identifier=self.identifier,
            specs_tags=self.specs_tags,
            external_docs=self.external_docs,
        ).to_json()

    def jsonable(self) -> Any:
        return get_app_schema(
            self.broker,
            title=self.title,
            app_version=self.version,
            schema_version=self.schema_version,
            description=self.description,
            terms_of_service=self.terms_of_service,
            contact=self.contact,
            license=self.license,
            identifier=self.identifier,
            specs_tags=self.specs_tags,
            external_docs=self.external_docs,
        ).to_jsonable()

    def yaml(self) -> str:
        return get_app_schema(
            self.broker,
            title=self.title,
            app_version=self.version,
            schema_version=self.schema_version,
            description=self.description,
            terms_of_service=self.terms_of_service,
            contact=self.contact,
            license=self.license,
            identifier=self.identifier,
            specs_tags=self.specs_tags,
            external_docs=self.external_docs,
        ).to_yaml()
