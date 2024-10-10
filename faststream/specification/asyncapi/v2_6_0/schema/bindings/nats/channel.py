"""AsyncAPI NATS bindings.

References: https://github.com/asyncapi/bindings/tree/master/nats
"""

from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream.specification import schema as spec


class ChannelBinding(BaseModel):
    """A class to represent channel binding.

    Attributes:
        subject : subject of the channel binding
        queue : optional queue for the channel binding
        bindingVersion : version of the channel binding, default is "custom"
    """

    subject: str
    queue: Optional[str] = None
    bindingVersion: str = "custom"

    @classmethod
    def from_spec(cls, binding: spec.bindings.nats.ChannelBinding) -> Self:
        return cls(
            subject=binding.subject,
            queue=binding.queue,
            bindingVersion=binding.bindingVersion,
        )


def from_spec(binding: spec.bindings.nats.ChannelBinding) -> ChannelBinding:
    return ChannelBinding.from_spec(binding)
