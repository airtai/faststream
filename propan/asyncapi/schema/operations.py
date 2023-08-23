from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from propan._compat import PYDANTIC_V2
from propan.asyncapi.schema.bindings import OperationBinding
from propan.asyncapi.schema.message import Message
from propan.asyncapi.schema.utils import ExternalDocs, ExternalDocsDict, Tag, TagDict


class Operation(BaseModel):
    operationId: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None

    bindings: Optional[OperationBinding] = None

    message: Message

    security: Optional[Dict[str, List[str]]] = None

    # TODO
    # traits

    tags: Optional[List[Union[Tag, TagDict, Dict[str, Any]]]] = None
    externalDocs: Optional[Union[ExternalDocs, ExternalDocsDict, Dict[str, Any]]] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
