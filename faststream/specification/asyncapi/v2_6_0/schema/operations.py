from typing import Dict, List, Optional, Union

from pydantic import BaseModel
from typing_extensions import Self

from faststream._compat import PYDANTIC_V2
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings import OperationBinding
from faststream.specification.asyncapi.v2_6_0.schema.bindings.main import (
    from_spec as channel_or_operation_binding_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.message import Message
from faststream.specification.asyncapi.v2_6_0.schema.message import (
    from_spec as message_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.tag import Tag
from faststream.specification.asyncapi.v2_6_0.schema.tag import (
    from_spec as tag_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.utils import (
    Reference,
)
from faststream.types import AnyDict


class Operation(BaseModel):
    """A class to represent an operation.

    Attributes:
        operationId : ID of the operation
        summary : summary of the operation
        description : description of the operation
        bindings : bindings of the operation
        message : message of the operation
        security : security details of the operation
        tags : tags associated with the operation

    """

    operationId: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None

    bindings: Optional[OperationBinding] = None

    message: Union[Message, Reference]

    security: Optional[Dict[str, List[str]]] = None

    # TODO
    # traits

    tags: Optional[List[Union[Tag, AnyDict]]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"

    @classmethod
    def from_spec(cls, operation: spec.operation.Operation) -> Self:
        return cls(
            operationId=operation.operationId,
            summary=operation.summary,
            description=operation.description,

            bindings=channel_or_operation_binding_from_spec(operation.bindings)
            if operation.bindings is not None else None,

            message=message_from_spec(operation.message)
            if operation.message is not None else None,

            tags=[tag_from_spec(tag) for tag in operation.tags]
            if operation.tags is not None else None,
        )


def from_spec(operation: spec.operation.Operation) -> Operation:
    return Operation.from_spec(operation)
