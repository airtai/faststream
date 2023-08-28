from abc import ABC
from dataclasses import dataclass, field
from typing import Optional

from faststream.broker.publisher import BasePublisher
from faststream.broker.types import MsgType
from faststream.rabbit.shared.schemas import BaseRMQInformation
from faststream.rabbit.shared.types import TimeoutType
from faststream.types import AnyDict


@dataclass
class ABCPublisher(ABC, BasePublisher[MsgType], BaseRMQInformation):
    routing_key: str = ""
    mandatory: bool = True
    immediate: bool = False
    persist: bool = False
    timeout: TimeoutType = None
    reply_to: Optional[str] = None
    message_kwargs: AnyDict = field(default_factory=dict)


QueueName = str
ExchangeName = str
