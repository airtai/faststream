from typing import List, Optional, Union

import typing_extensions
from pydantic import BaseModel

from faststream._internal._compat import PYDANTIC_V2
from faststream._internal.basic_types import AnyDict
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.tag import Tag
from faststream.specification.asyncapi.v2_6_0.schema.tag import (
    from_spec as tag_from_spec,
)


class CorrelationId(BaseModel):
    """A class to represent a correlation ID.

    Attributes:
        description : optional description of the correlation ID
        location : location of the correlation ID

    Configurations:
        extra : allows extra fields in the correlation ID model

    """

    description: Optional[str] = None
    location: str

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"

    @classmethod
    def from_spec(cls, cor_id: spec.message.CorrelationId) -> typing_extensions.Self:
        return cls(
            description=cor_id.description,
            location=cor_id.location,
        )


class Message(BaseModel):
    """A class to represent a message.

    Attributes:
        title : title of the message
        name : name of the message
        summary : summary of the message
        description : description of the message
        messageId : ID of the message
        correlationId : correlation ID of the message
        contentType : content type of the message
        payload : dictionary representing the payload of the message
        tags : list of tags associated with the message

    """

    title: Optional[str] = None
    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    messageId: Optional[str] = None
    correlationId: Optional[CorrelationId] = None
    contentType: Optional[str] = None

    payload: AnyDict
    # TODO:
    # headers
    # schemaFormat
    # bindings
    # examples
    # traits

    tags: Optional[List[Union[Tag, AnyDict]]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"

    @classmethod
    def from_spec(cls, message: spec.message.Message) -> typing_extensions.Self:
        return cls(
            title=message.title,
            name=message.name,
            summary=message.summary,
            description=message.description,
            messageId=message.messageId,
            correlationId=CorrelationId.from_spec(message.correlationId)
            if message.correlationId is not None
            else None,
            contentType=message.contentType,
            payload=message.payload,
            tags=[tag_from_spec(tag) for tag in message.tags]
            if message.tags is not None
            else None,
        )


def from_spec(message: spec.message.Message) -> Message:
    return Message.from_spec(message)
