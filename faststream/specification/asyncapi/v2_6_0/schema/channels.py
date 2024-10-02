from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream._internal._compat import PYDANTIC_V2
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings import (
    ChannelBinding,
    channel_binding_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.operations import (
    Operation,
    from_spec as operation_from_spec,
)


class Channel(BaseModel):
    """A class to represent a channel.

    Attributes:
        description : optional description of the channel
        servers : optional list of servers associated with the channel
        bindings : optional channel binding
        subscribe : optional operation for subscribing to the channel
        publish : optional operation for publishing to the channel

    Configurations:
        model_config : configuration for the model (only applicable for Pydantic version 2)
        Config : configuration for the class (only applicable for Pydantic version 1)

    """

    description: Optional[str] = None
    servers: Optional[list[str]] = None
    bindings: Optional[ChannelBinding] = None
    subscribe: Optional[Operation] = None
    publish: Optional[Operation] = None

    # TODO:
    # parameters: Optional[Parameter] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"

    @classmethod
    def from_spec(cls, channel: spec.channel.Channel) -> Self:
        return cls(
            description=channel.description,
            servers=channel.servers,
            bindings=channel_binding_from_spec(channel.bindings)
            if channel.bindings is not None
            else None,
            subscribe=operation_from_spec(channel.subscribe)
            if channel.subscribe is not None
            else None,
            publish=operation_from_spec(channel.publish)
            if channel.publish is not None
            else None,
        )


def from_spec(channel: spec.channel.Channel) -> Channel:
    return Channel.from_spec(channel)
