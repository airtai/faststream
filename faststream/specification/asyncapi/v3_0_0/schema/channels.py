from typing import Dict, List, Optional, Union

from pydantic import BaseModel
from typing_extensions import Self

from faststream._compat import PYDANTIC_V2
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings import ChannelBinding
from faststream.specification.asyncapi.v2_6_0.schema.bindings.main import (
    channel_binding_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.message import Message
from faststream.specification.asyncapi.v2_6_0.schema.message import (
    from_spec as message_from_spec,
)
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

    @classmethod
    def from_spec(
        cls,
        channel: spec.channel.Channel,
        message: spec.message.Message,
        channel_name: str,
        message_name: str,
    ) -> Self:
        return cls(
            address=channel_name,
            messages={
                message_name: message_from_spec(message),
            },
            description=channel.description,
            servers=channel.servers,
            bindings=channel_binding_from_spec(channel.bindings)
            if channel.bindings
            else None,
        )


def from_spec(
    channel: spec.channel.Channel,
    message: spec.message.Message,
    channel_name: str,
    message_name: str,
) -> Channel:
    return Channel.from_spec(channel, message, channel_name, message_name)
