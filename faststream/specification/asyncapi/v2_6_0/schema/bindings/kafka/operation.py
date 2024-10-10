"""AsyncAPI Kafka bindings.

References: https://github.com/asyncapi/bindings/tree/master/kafka
"""

from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream._internal.basic_types import AnyDict
from faststream.specification import schema as spec


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        groupId : optional dictionary representing the group ID
        clientId : optional dictionary representing the client ID
        replyTo : optional dictionary representing the reply-to
        bindingVersion : version of the binding (default: "0.4.0")
    """

    groupId: Optional[AnyDict] = None
    clientId: Optional[AnyDict] = None
    replyTo: Optional[AnyDict] = None
    bindingVersion: str = "0.4.0"

    @classmethod
    def from_spec(cls, binding: spec.bindings.kafka.OperationBinding) -> Self:
        return cls(
            groupId=binding.groupId,
            clientId=binding.clientId,
            replyTo=binding.replyTo,
            bindingVersion=binding.bindingVersion,
        )


def from_spec(binding: spec.bindings.kafka.OperationBinding) -> OperationBinding:
    return OperationBinding.from_spec(binding)
