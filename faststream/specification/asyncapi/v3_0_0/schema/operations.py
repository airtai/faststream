from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel
from typing_extensions import Self

from faststream._compat import PYDANTIC_V2
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings import OperationBinding
from faststream.specification.asyncapi.v2_6_0.schema.bindings.main import (
    operation_binding_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.tag import Tag
from faststream.specification.asyncapi.v2_6_0.schema.utils import (
    Reference,
)
from faststream.specification.asyncapi.v3_0_0.schema.channels import Channel
from faststream.types import AnyDict


class Action(str, Enum):
    SEND = "send"
    RECEIVE = "receive"


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
    action: Action
    summary: Optional[str] = None
    description: Optional[str] = None

    bindings: Optional[OperationBinding] = None

    messages: List[Reference]
    channel: Union[Channel, Reference]

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
    def from_spec(cls, operation: spec.operation.Operation, action: Action, channel_name: str) -> Self:
        return cls(
            action=action,
            summary=operation.summary,
            description=operation.description,

            bindings=operation_binding_from_spec(operation.bindings)
            if operation.bindings else None,

            messages=[
                Reference(
                    **{
                        "$ref": f"#/channels/{channel_name}/messages/SubscribeMessage"
                                if action is Action.RECEIVE else
                                f"#/channels/{channel_name}/messages/Message"
                    },
                )
            ],

            channel=Reference(
                **{"$ref": f"#/channels/{channel_name}"},
            ),

            security=operation.security,
        )


def from_spec(operation: spec.operation.Operation, action: Action, channel_name: str) -> Operation:
    return Operation.from_spec(operation, action, channel_name)
