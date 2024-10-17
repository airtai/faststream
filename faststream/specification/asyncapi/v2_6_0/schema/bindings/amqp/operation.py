"""AsyncAPI AMQP bindings.

References: https://github.com/asyncapi/bindings/tree/master/amqp
"""

from typing import Optional, overload

from pydantic import BaseModel, PositiveInt
from typing_extensions import Self

from faststream.specification.schema.bindings import amqp


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        cc : optional string representing the cc
        ack : boolean indicating if the operation is acknowledged
        replyTo : optional dictionary representing the replyTo
        bindingVersion : string representing the binding version
    """

    cc: Optional[str] = None
    ack: bool = True
    replyTo: Optional[str] = None
    deliveryMode: Optional[int] = None
    mandatory: Optional[bool] = None
    priority: Optional[PositiveInt] = None
    bindingVersion: str = "0.2.0"

    @overload
    @classmethod
    def from_sub(cls, binding: None) -> None: ...

    @overload
    @classmethod
    def from_sub(cls, binding: amqp.OperationBinding) -> Self: ...

    @classmethod
    def from_sub(cls, binding: Optional[amqp.OperationBinding]) -> Optional[Self]:
        if binding is None:
            return None

        return cls(
            cc=binding.cc,
            ack=binding.ack,
            replyTo=binding.reply_to,
            deliveryMode=binding.delivery_mode,
            mandatory=binding.mandatory,
            priority=binding.priority,
        )

    @overload
    @classmethod
    def from_pub(cls, binding: None) -> None: ...

    @overload
    @classmethod
    def from_pub(cls, binding: amqp.OperationBinding) -> Self: ...

    @classmethod
    def from_pub(cls, binding: Optional[amqp.OperationBinding]) -> Optional[Self]:
        if binding is None:
            return None

        return cls(
            cc=binding.cc,
            ack=binding.ack,
            replyTo=binding.reply_to,
            deliveryMode=binding.delivery_mode,
            mandatory=binding.mandatory,
            priority=binding.priority,
        )
