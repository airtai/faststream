from typing import Any, Dict, Optional

from pydantic import BaseModel, PositiveInt


class ServerBinding(BaseModel):
    bindingVersion: str = "0.4.0"


class ChannelBinding(BaseModel):
    topic: Optional[str] = None
    partitions: Optional[PositiveInt] = None
    replicas: Optional[PositiveInt] = None
    # TODO:
    # topicConfiguration
    bindingVersion: str = "0.4.0"


class OperationBinding(BaseModel):
    groupId: Optional[Dict[str, Any]] = None
    clientId: Optional[Dict[str, Any]] = None
    replyTo: Optional[Dict[str, Any]] = None
    bindingVersion: str = "0.4.0"
