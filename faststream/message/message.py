from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    TypeVar,
    Union,
)
from uuid import uuid4

from .source_type import SourceType

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, DecodedMessage

# prevent circular imports
MsgType = TypeVar("MsgType")


class AckStatus(str, Enum):
    acked = "acked"
    nacked = "nacked"
    rejected = "rejected"


class StreamMessage(Generic[MsgType]):
    """Generic class to represent a stream message."""

    def __init__(
        self,
        raw_message: "MsgType",
        body: Union[bytes, Any],
        *,
        headers: Optional["AnyDict"] = None,
        reply_to: str = "",
        batch_headers: Optional[list["AnyDict"]] = None,
        path: Optional["AnyDict"] = None,
        content_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        source_type: SourceType = SourceType.Consume,
    ) -> None:
        self.raw_message = raw_message
        self.body = body
        self.reply_to = reply_to
        self.content_type = content_type
        self._source_type = source_type

        self.headers = headers or {}
        self.batch_headers = batch_headers or []
        self.path = path or {}
        self.correlation_id = correlation_id or str(uuid4())
        self.message_id = message_id or self.correlation_id

        # Setup later
        self._decoded_body: Optional[DecodedMessage] = None
        self.committed: Optional[AckStatus] = None
        self.processed = False

    def __repr__(self) -> str:
        inner = ", ".join(
            filter(
                bool,
                (
                    f"body={self.body}",
                    f"content_type={self.content_type}",
                    f"message_id={self.message_id}",
                    f"correlation_id={self.correlation_id}",
                    f"reply_to={self.reply_to}" if self.reply_to else "",
                    f"headers={self.headers}",
                    f"path={self.path}",
                    f"committed={self.committed}",
                    f"raw_message={self.raw_message}",
                ),
            ),
        )

        return f"{self.__class__.__name__}({inner})"

    async def decode(self) -> Optional["DecodedMessage"]:
        """Serialize the message by lazy decoder."""
        # TODO: make it lazy after `decoded_body` removed
        return self._decoded_body

    async def ack(self) -> None:
        if self.committed is None:
            self.committed = AckStatus.acked

    async def nack(self) -> None:
        if self.committed is None:
            self.committed = AckStatus.nacked

    async def reject(self) -> None:
        if self.committed is None:
            self.committed = AckStatus.rejected
