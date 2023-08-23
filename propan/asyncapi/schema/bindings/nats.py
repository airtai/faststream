from typing import Any, Dict, Optional

from pydantic import BaseModel


class ServerBinding(BaseModel):
    bindingVersion: str = "custom"


class ChannelBinding(BaseModel):
    subject: str
    queue: Optional[str] = None
    bindingVersion: str = "custom"


class OperationBinding(BaseModel):
    replyTo: Optional[Dict[str, Any]] = None
    bindingVersion: str = "custom"
