from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel


class ServerBinding(BaseModel):
    bindingVersion: str = "custom"


class ChannelBinding(BaseModel):
    channel: str
    method: Literal["ssubscribe", "psubscribe", "subscribe"] = "subscribe"
    bindingVersion: str = "custom"


class OperationBinding(BaseModel):
    replyTo: Optional[Dict[str, Any]] = None
    bindingVersion: str = "custom"
