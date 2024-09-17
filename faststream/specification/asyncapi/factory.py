from typing import TYPE_CHECKING, Any, Literal, Optional, Sequence, Union

from faststream._internal.broker.broker import BrokerUsecase
from faststream.specification.asyncapi.base.asyncapi import AsyncAPIProto
from faststream.specification.asyncapi.base.schema import BaseSchema
from faststream.specification.asyncapi.v2_6_0.asyncapi import AsyncAPI2
from faststream.specification.asyncapi.v3_0_0.asyncapi import AsyncAPI3

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, AnyHttpUrl
    from faststream.specification.schema.contact import Contact, ContactDict
    from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
    from faststream.specification.schema.license import License, LicenseDict
    from faststream.specification.schema.tag import Tag, TagDict


class AsyncAPI(AsyncAPIProto):
    def __new__(  # type: ignore[misc]
            cls,
            broker: BrokerUsecase[Any, Any],
            /,
            title: str = "FastStream",
            app_version: str = "0.1.0",
            schema_version: Union[Literal["3.0.0", "2.6.0"], str] = "2.6.0",
            description: str = "",
            terms_of_service: Optional["AnyHttpUrl"] = None,
            license: Optional[Union["License", "LicenseDict", "AnyDict"]] = None,
            contact: Optional[Union["Contact", "ContactDict", "AnyDict"]] = None,
            tags: Optional[Sequence[Union["Tag", "TagDict", "AnyDict"]]] = None,
            external_docs: Optional[Union["ExternalDocs", "ExternalDocsDict", "AnyDict"]] = None,
            identifier: Optional[str] = None,
    ) -> AsyncAPIProto:
        if schema_version.startswith("3.0."):
            return AsyncAPI3(
                broker,
                title=title,
                app_version=app_version,
                schema_version=schema_version,
                description=description,
                terms_of_service=terms_of_service,
                contact=contact,
                license=license,
                identifier=identifier,
                tags=tags,
                external_docs=external_docs,
            )
        elif schema_version.startswith("2.6."):
            return AsyncAPI2(
                broker,
                title=title,
                app_version=app_version,
                schema_version=schema_version,
                description=description,
                terms_of_service=terms_of_service,
                contact=contact,
                license=license,
                identifier=identifier,
                tags=tags,
                external_docs=external_docs,
            )
        else:
            raise NotImplementedError(f"Unsupported schema version: {schema_version}")

    def json(self) -> str:  # type: ignore[empty-body]
        pass

    def jsonable(self) -> Any:
        pass

    def yaml(self) -> str:  # type: ignore[empty-body]
        pass

    def schema(self) -> BaseSchema:  # type: ignore[empty-body]
        pass
