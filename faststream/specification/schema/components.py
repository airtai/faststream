from typing import (
    Any,
    Optional,
)

from pydantic import BaseModel

from faststream._internal._compat import (
    PYDANTIC_V2,
)
from faststream.specification.schema.message import Message


class Components(BaseModel):
    """A class to represent components in a system.

    Attributes:
        messages : Optional dictionary of messages
        schemas : Optional dictionary of schemas

    Note:
        The following attributes are not implemented yet:
        - servers
        - serverVariables
        - channels
        - securitySchemes
    """

    messages: Optional[dict[str, Message]] = None
    schemas: Optional[dict[str, dict[str, Any]]] = None
    securitySchemes: Optional[dict[str, dict[str, Any]]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
