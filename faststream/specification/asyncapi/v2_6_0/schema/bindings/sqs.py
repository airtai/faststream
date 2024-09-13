"""AsyncAPI SQS bindings.

References: https://github.com/asyncapi/bindings/tree/master/sqs
"""

from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream._internal.basic_types import AnyDict
from faststream.specification import schema as spec


class ChannelBinding(BaseModel):
    """A class to represent channel binding.

    Attributes:
        queue : a dictionary representing the queue
        bindingVersion : a string representing the binding version (default: "custom")
    """

    queue: AnyDict
    bindingVersion: str = "custom"

    @classmethod
    def from_spec(cls, binding: spec.bindings.sqs.ChannelBinding) -> Self:
        return cls(
            queue=binding.queue,
            bindingVersion=binding.bindingVersion,
        )


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        replyTo : optional dictionary containing reply information
        bindingVersion : version of the binding, default is "custom"
    """

    replyTo: Optional[AnyDict] = None
    bindingVersion: str = "custom"

    @classmethod
    def from_spec(cls, binding: spec.bindings.sqs.OperationBinding) -> Self:
        return cls(
            replyTo=binding.replyTo,
            bindingVersion=binding.bindingVersion,
        )
