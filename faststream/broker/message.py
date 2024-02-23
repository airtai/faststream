from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar, Union
from uuid import uuid4

from faststream.types import AnyDict, DecodedMessage

MsgType = TypeVar("MsgType")


@dataclass
class StreamMessage(Generic[MsgType]):
    """Generic class to represent a stream message.

    Attributes:
        raw_message : the raw message
        body : the body of the message, can be bytes or any other type
        decoded_body : the decoded message body, if applicable
        content_type : the content type of the message
        reply_to : the reply-to address of the message
        headers : additional headers of the message
        message_id : the unique identifier of the message
        correlation_id : the correlation identifier of the message
        processed : a flag indicating whether the message has been processed or not
    """

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

    async def ack(self, **kwargs: Any) -> None:
        self.committed = True

    async def nack(self, **kwargs: Any) -> None:
        self.committed = True

    async def reject(self, **kwargs: Any) -> None:
        self.committed = True
