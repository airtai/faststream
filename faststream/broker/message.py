import json
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, Sequence, Tuple, TypeVar, Union
from uuid import uuid4

from faststream._compat import dump_json, json_loads
from faststream.constants import ContentTypes
from faststream.types import AnyDict, DecodedMessage, SendableMessage

# prevent circular imports
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


def decode_message(message: StreamMessage[Any]) -> DecodedMessage:
    """Decodes a message."""
    body: Any = getattr(message, "body", message)
    m: DecodedMessage = body

    if content_type := getattr(message, "content_type", None):
        if ContentTypes.text.value in content_type:
            m = body.decode()
        elif ContentTypes.json.value in content_type:  # pragma: no branch
            m = json_loads(body)
        else:
            with suppress(json.JSONDecodeError):
                m = json_loads(body)
    else:
        with suppress(json.JSONDecodeError):
            m = json_loads(body)

    return m


def encode_message(
    msg: Union[Sequence[SendableMessage], SendableMessage],
) -> Tuple[bytes, Optional[str]]:
    """Encodes a message."""
    if msg is None:
        return (
            b"",
            None,
        )

    if isinstance(msg, bytes):
        return (
            msg,
            None,
        )

    if isinstance(msg, str):
        return (
            msg.encode(),
            ContentTypes.text.value,
        )

    return (
        dump_json(msg),
        ContentTypes.json.value,
    )
