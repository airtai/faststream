from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from faststream.specification.schema.bindings import OperationBinding
from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
from faststream.specification.schema.message import Message
from faststream.specification.schema.tag import Tag, TagDict


@dataclass
class Operation:
    """A class to represent an operation.

    Attributes:
        operationId : ID of the operation
        summary : summary of the operation
        description : description of the operation
        bindings : bindings of the operation
        message : message of the operation
        security : security details of the operation
        tags : tags associated with the operation
        externalDocs : external documentation for the operation

    """

    message: Message

    operationId: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None

    bindings: Optional[OperationBinding] = None

    security: Optional[Dict[str, List[str]]] = None

    tags: Optional[List[Union[Tag, TagDict, Dict[str, Any]]]] = None
    externalDocs: Optional[Union[ExternalDocs, ExternalDocsDict, Dict[str, Any]]] = None

