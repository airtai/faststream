from typing import Any, Optional, Union, Sequence

from faststream._internal.basic_types import AnyHttpUrl, AnyDict
from faststream._internal.broker.broker import BrokerUsecase
from faststream.specification.asyncapi.base.asyncapiproto import AsyncAPIProto
from faststream.specification.asyncapi.v2_6_0.asyncapi import AsyncAPI2
from faststream.specification.asyncapi.v3_0_0.asyncapi import AsyncAPI3
from faststream.specification.schema.contact import Contact, ContactDict
from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
from faststream.specification.schema.license import License, LicenseDict
from faststream.specification.schema.tag import Tag, TagDict


class AsyncAPI(AsyncAPIProto):
    def __new__(
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
    ) -> AsyncAPIProto:
        if schema_version.startswith("3.0."):
            return AsyncAPI3(
                broker,
                title=title,
                version=version,
                schema_version=schema_version,
                description=description,
                terms_of_service=terms_of_service,
                contact=contact,
                license=license,
                identifier=identifier,
                specs_tags=specs_tags,
                external_docs=external_docs,
            )
        elif schema_version.startswith("2.6."):
            return AsyncAPI2(
                broker,
                title=title,
                version=version,
                schema_version=schema_version,
                description=description,
                terms_of_service=terms_of_service,
                contact=contact,
                license=license,
                identifier=identifier,
                specs_tags=specs_tags,
                external_docs=external_docs,
            )
        else:
            raise NotImplementedError(f"Unsupported schema version: {schema_version}")
