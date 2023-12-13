from typing import List, Optional

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.asyncapi.schema.bindings import ChannelBinding
from faststream.asyncapi.schema.operations import Operation
from faststream.asyncapi.schema.utils import Parameter


class Channel(BaseModel):
    """A class to represent a channel.

    Attributes:
        description : optional description of the channel
        servers : optional list of servers associated with the channel
        bindings : optional channel binding
        subscribe : optional operation for subscribing to the channel
        publish : optional operation for publishing to the channel
        parameters : optional parameters associated with the channel

    Configurations:
        model_config : configuration for the model (only applicable for Pydantic version 2)
        Config : configuration for the class (only applicable for Pydantic version 1)

    """

    description: Optional[str] = None
    servers: Optional[List[str]] = None
    bindings: Optional[ChannelBinding] = None
    subscribe: Optional[Operation] = None
    publish: Optional[Operation] = None
    parameters: Optional[Parameter] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
