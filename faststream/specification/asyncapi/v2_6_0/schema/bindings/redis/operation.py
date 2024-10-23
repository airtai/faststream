"""AsyncAPI Redis bindings.

References: https://github.com/asyncapi/bindings/tree/master/redis
"""

from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream._internal.basic_types import AnyDict
from faststream.specification import schema as spec


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        replyTo : optional dictionary containing reply information
        bindingVersion : version of the binding (default is "custom")
    """

    replyTo: Optional[AnyDict] = None
    bindingVersion: str = "custom"

    @classmethod
    def from_spec(cls, binding: spec.bindings.redis.OperationBinding) -> Self:
        return cls(
            replyTo=binding.replyTo,
            bindingVersion=binding.bindingVersion,
        )


def from_spec(binding: spec.bindings.redis.OperationBinding) -> OperationBinding:
    return OperationBinding.from_spec(binding)
