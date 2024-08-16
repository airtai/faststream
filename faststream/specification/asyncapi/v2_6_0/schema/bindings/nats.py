"""AsyncAPI NATS bindings.

References: https://github.com/asyncapi/bindings/tree/master/nats
"""

from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream.specification import schema as spec
from faststream.types import AnyDict


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


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        replyTo : optional dictionary containing reply information
        bindingVersion : version of the binding (default is "custom")
    """

    replyTo: Optional[AnyDict] = None
    bindingVersion: str = "custom"

    @classmethod
    def from_spec(cls, binding: spec.bindings.nats.OperationBinding) -> Self:
        return cls(
            replyTo=binding.replyTo,
            bindingVersion=binding.bindingVersion,
        )
