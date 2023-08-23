from abc import ABC
from dataclasses import dataclass
from typing import Dict, Optional

from propan.broker.publisher import BasePublisher
from propan.broker.types import MsgType


@dataclass
class ABCPublisher(ABC, BasePublisher[MsgType]):
    topic: str = ""
    key: Optional[bytes] = None
    partition: Optional[int] = None
    timestamp_ms: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    reply_to: Optional[str] = ""
