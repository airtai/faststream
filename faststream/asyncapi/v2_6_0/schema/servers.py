from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.asyncapi.schema.bindings import ServerBinding
from faststream.asyncapi.schema.servers import SecurityRequirement, ServerVariable
from faststream.asyncapi.schema.utils import Reference, Tag, TagDict


class Server(BaseModel):
    """A class to represent a server.

    Attributes:
        url : URL of the server
        protocol : protocol used by the server
        description : optional description of the server
        protocolVersion : optional version of the protocol used by the server
        tags : optional list of tags associated with the server
        security : optional security requirement for the server
        variables : optional dictionary of server variables
        bindings : optional server binding

    Note:
        The attributes `description`, `protocolVersion`, `tags`, `security`, `variables`, and `bindings` are all optional.

    Configurations:
        If `PYDANTIC_V2` is True, the model configuration is set to allow extra attributes.
        Otherwise, the `Config` class is defined with the `extra` attribute set to "allow".

    """

    url: str
    protocol: str
    description: Optional[str] = None
    protocolVersion: Optional[str] = None
    tags: Optional[List[Union[Tag, TagDict, Dict[str, Any]]]] = None
    security: Optional[SecurityRequirement] = None
    variables: Optional[Dict[str, Union[ServerVariable, Reference]]] = None
    bindings: Optional[Union[ServerBinding, Reference]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
