from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

<<<<<<<< HEAD:faststream/specification/schema/operation.py
from faststream.specification.schema.bindings import OperationBinding
from faststream.specification.schema.message import Message
from faststream.specification.schema.tag import Tag
========
from faststream.specification.bindings import OperationBinding
from faststream.specification.docs import ExternalDocs, ExternalDocsDict
from faststream.specification.message import Message
from faststream.specification.tag import Tag, TagDict
>>>>>>>> 3361c325 (mypy satisfied):faststream/specification/operation.py


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

    """

    message: Message

    operationId: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None

    bindings: Optional[OperationBinding] = None

    security: Optional[Dict[str, List[str]]] = None

    tags: Optional[List[Union[Tag, Dict[str, Any]]]] = None
