from typing import (
    List,
    Optional,
    Union,
)

from pydantic import AnyHttpUrl

from faststream.specification.asyncapi.base.schema import BaseInfo
from faststream.specification.asyncapi.v2_6_0.schema import (
    Contact,
    ExternalDocs,
    License,
    Tag,
)
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
    contact: Optional[Union[Contact, AnyDict]] = None
    license: Optional[Union[License, AnyDict]] = None
    tags: Optional[List[Union["Tag", "AnyDict"]]] = None
    externalDocs: Optional[Union["ExternalDocs", "AnyDict"]] = None
