from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.asyncapi.schema.utils import (
    ExternalDocs,
    Tag,
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
        externalDocs : external documentation associated with the message

    """

    title: Optional[str] = None
    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    messageId: Optional[str] = None
    correlationId: Optional[CorrelationId] = None
    contentType: Optional[str] = None

    payload: Dict[str, Any]
    # TODO:
    # headers
    # schemaFormat
    # bindings
    # examples
    # traits

    tags: Optional[List[Union[Tag, Dict[str, Any]]]] = (
        None  # TODO: weird TagDict behavior
    )
    externalDocs: Optional[Union[ExternalDocs, Dict[str, Any]]] = (
        None  # TODO: weird ExternalDocsDict behavior
    )

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
