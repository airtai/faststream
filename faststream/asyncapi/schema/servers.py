from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.asyncapi.schema.bindings import ServerBinding
from faststream.asyncapi.schema.utils import Reference, Tag, TagDict

SecurityRequirement = List[Dict[str, List[str]]]


class ServerVariable(BaseModel):
    """A class to represent a server variable.

    Attributes:
        enum : list of possible values for the server variable (optional)
        default : default value for the server variable (optional)
        description : description of the server variable (optional)
        examples : list of example values for the server variable (optional)

    """

    enum: Optional[List[str]] = None
    default: Optional[str] = None
    description: Optional[str] = None
    examples: Optional[List[str]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


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
