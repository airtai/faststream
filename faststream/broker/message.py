from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar, Union
from uuid import uuid4

from faststream.types import AnyDict, DecodedMessage

MsgType = TypeVar("MsgType")


@dataclass
class StreamMessage(Generic[MsgType]):
    """Generic class to represent a stream message."""

    raw_message: "MsgType"

    body: Union[bytes, Any]
    decoded_body: Optional[DecodedMessage] = None
    headers: AnyDict = field(default_factory=dict)
    path: AnyDict = field(default_factory=dict)

    content_type: Optional[str] = None
    reply_to: str = ""
    message_id: str = field(default_factory=lambda: str(uuid4()))  # pragma: no cover
    correlation_id: str = field(
        default_factory=lambda: str(uuid4())  # pragma: no cover
    )

    processed: bool = field(default=False, init=False)
    committed: bool = field(default=False, init=False)

    async def ack(self) -> None:
        self.committed = True

    async def nack(self) -> None:
        self.committed = True

    async def reject(self) -> None:
        self.committed = True
