from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from faststream.specification.docs import ExternalDocs
from faststream.specification.tag import Tag


@dataclass
class CorrelationId:
    """Correlation ID specification.

    Attributes:
        description : optional description of the correlation ID
        location : location of the correlation ID

    Configurations:
        extra : allows extra fields in the correlation ID model

    """

    location: str
    description: Optional[str] = None


@dataclass
class Message:
    """Message specification.

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

    payload: Dict[str, Any]
    title: Optional[str] = None
    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    messageId: Optional[str] = None
    correlationId: Optional[CorrelationId] = None
    contentType: Optional[str] = None

    tags: Optional[List[Union[Tag, Dict[str, Any]]]] = (
        None
    )
    externalDocs: Optional[Union[ExternalDocs, Dict[str, Any]]] = (
        None
    )
