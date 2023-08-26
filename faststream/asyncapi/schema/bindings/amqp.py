from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class Queue(BaseModel):
    name: str
    durable: bool
    exclusive: bool
    autoDelete: bool
    vhost: str = "/"


class Exchange(BaseModel):
    name: Optional[str] = None
    type: Literal["default", "direct", "topic", "fanout", "headers"]
    durable: Optional[bool] = None
    autoDelete: Optional[bool] = None
    vhost: str = "/"


class ServerBinding(BaseModel):
    bindingVersion: str = "0.2.0"


class ChannelBinding(BaseModel):
    is_: Literal["queue", "routingKey"] = Field(..., alias="is")
    bindingVersion: str = "0.2.0"
    queue: Optional[Queue] = None
    exchange: Optional[Exchange] = None


class OperationBinding(BaseModel):
    cc: Optional[str] = None
    ack: bool = True
    replyTo: Optional[Dict[str, Any]] = None
    bindingVersion: str = "0.2.0"
