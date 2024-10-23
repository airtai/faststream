from typing import (
    Optional,
    Union,
)

from pydantic import AnyHttpUrl

from faststream._internal.basic_types import AnyDict
from faststream.specification.asyncapi.v2_6_0.schema.contact import Contact
from faststream.specification.asyncapi.v2_6_0.schema.license import License
from faststream.specification.base.info import BaseInfo


class Info(BaseInfo):
    """A class to represent information.

    Attributes:
        title : title of the information
        version : version of the information (default: "1.0.0")
        description : description of the information (default: "")
        termsOfService : terms of service for the information (default: None)
        contact : contact information for the information (default: None)
        license : license information for the information (default: None)
    """

    termsOfService: Optional[AnyHttpUrl] = None
    contact: Optional[Union[Contact, AnyDict]] = None
    license: Optional[Union[License, AnyDict]] = None
