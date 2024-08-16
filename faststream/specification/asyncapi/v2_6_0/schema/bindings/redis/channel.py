"""AsyncAPI Redis bindings.

References: https://github.com/asyncapi/bindings/tree/master/redis
"""

from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream.specification import schema as spec


class ChannelBinding(BaseModel):
    """A class to represent channel binding.

    Attributes:
        channel : the channel name
        method : the method used for binding (ssubscribe, psubscribe, subscribe)
        bindingVersion : the version of the binding
    """

    channel: str
    method: Optional[str] = None
    group_name: Optional[str] = None
    consumer_name: Optional[str] = None
    bindingVersion: str = "custom"

    @classmethod
    def from_spec(cls, binding: spec.bindings.redis.ChannelBinding) -> Self:
        return cls(
            channel=binding.channel,
            method=binding.method,
            group_name=binding.group_name,
            consumer_name=binding.consumer_name,
            bindingVersion=binding.bindingVersion,
        )


def from_spec(binding: spec.bindings.redis.ChannelBinding) -> ChannelBinding:
    return ChannelBinding.from_spec(binding)
