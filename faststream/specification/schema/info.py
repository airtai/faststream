from typing import (
    Any,
    Dict,
    Optional,
    Union,
)

from pydantic import AnyHttpUrl, BaseModel

from faststream.specification.schema.contact import Contact, ContactDict
from faststream.specification.schema.license import License, LicenseDict


class Info(BaseModel):
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
    contact: Optional[Union[Contact, ContactDict, Dict[str, Any]]] = None
    license: Optional[Union[License, LicenseDict, Dict[str, Any]]] = None
