from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.specification.asyncapi.v2_6_0.schema.bindings import ChannelBinding
from faststream.specification.asyncapi.v2_6_0.schema.message import Message
from faststream.specification.asyncapi.v2_6_0.schema.utils import Reference


class Channel(BaseModel):
    """A class to represent a channel.

    Attributes:
        address: A string representation of this channel's address.
        description : optional description of the channel
        servers : optional list of servers associated with the channel
        bindings : optional channel binding
        parameters : optional parameters associated with the channel

    Configurations:
        model_config : configuration for the model (only applicable for Pydantic version 2)
        Config : configuration for the class (only applicable for Pydantic version 1)

    """

    address: str
    description: Optional[str] = None
    servers: Optional[List[Dict[str, str]]] = None
    messages: Dict[str, Union[Message, Reference]]
    bindings: Optional[ChannelBinding] = None

    # TODO:
    # parameters: Optional[Parameter] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
