from typing import (
    List,
    Optional,
    Union,
)

from pydantic import AnyHttpUrl

from faststream.specification.asyncapi.base.schema import BaseInfo
from faststream.specification.asyncapi.v2_6_0.schema.docs import ExternalDocs
from faststream.specification.asyncapi.v2_6_0.schema.info import (
    Contact,
    ContactDict,
    License,
    LicenseDict,
)
from faststream.specification.asyncapi.v2_6_0.schema.tag import Tag
from faststream.types import (
    AnyDict,
)


class Info(BaseInfo):
    """A class to represent information.

    Attributes:
        termsOfService : terms of service for the information (default: None)
        contact : contact information for the information (default: None)
        license : license information for the information (default: None)
        tags : optional list of tags
        externalDocs : optional external documentation

    """

    termsOfService: Optional[AnyHttpUrl] = None
    contact: Optional[Union[Contact, ContactDict, AnyDict]] = None
    license: Optional[Union[License, LicenseDict, AnyDict]] = None
    tags: Optional[List[Union["Tag", "AnyDict"]]] = None
    externalDocs: Optional[
            Union["ExternalDocs", "AnyDict"]
    ] = None
