from typing import Any, Dict, Optional

from pydantic import BaseModel


class ServerBinding(BaseModel):
    bindingVersion: str = "custom"


class ChannelBinding(BaseModel):
    queue: Dict[str, Any]
    bindingVersion: str = "custom"


class OperationBinding(BaseModel):
    replyTo: Optional[Dict[str, Any]] = None
    bindingVersion: str = "custom"
