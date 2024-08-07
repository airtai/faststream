from typing import (
    Any,
    Dict,
    Optional,
    Union,
)

from pydantic import AnyHttpUrl

from faststream.asyncapi.schema.info import (
    BaseInfo,
    Contact,
    ContactDict,
    License,
    LicenseDict,
)


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
    contact: Optional[Union[Contact, ContactDict, Dict[str, Any]]] = None
    license: Optional[Union[License, LicenseDict, Dict[str, Any]]] = None
