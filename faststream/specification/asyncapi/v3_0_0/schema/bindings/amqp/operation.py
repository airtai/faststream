"""AsyncAPI AMQP bindings.

References: https://github.com/asyncapi/bindings/tree/master/amqp
"""

from typing import Optional

from pydantic import BaseModel, PositiveInt
from typing_extensions import Self

from faststream.specification import schema as spec


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        cc : optional string representing the cc
        ack : boolean indicating if the operation is acknowledged
        replyTo : optional dictionary representing the replyTo
        bindingVersion : string representing the binding version
    """

    cc: Optional[list[str]] = None
    ack: bool = True
    replyTo: Optional[str] = None
    deliveryMode: Optional[int] = None
    mandatory: Optional[bool] = None
    priority: Optional[PositiveInt] = None
    bindingVersion: str = "0.3.0"

    @classmethod
    def from_spec(cls, binding: spec.bindings.amqp.OperationBinding) -> Self:
        return cls(
            cc=[binding.cc] if binding.cc is not None else None,
            ack=binding.ack,
            replyTo=binding.replyTo,
            deliveryMode=binding.deliveryMode,
            mandatory=binding.mandatory,
            priority=binding.priority,
        )


def from_spec(binding: spec.bindings.amqp.OperationBinding) -> OperationBinding:
    return OperationBinding.from_spec(binding)
