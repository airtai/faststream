import json
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)
from uuid import uuid4

from faststream._compat import dump_json, json_loads
from faststream.constants import ContentTypes

if TYPE_CHECKING:
    from faststream.types import AnyDict, DecodedMessage, SendableMessage

# prevent circular imports
MsgType = TypeVar("MsgType")


def gen_cor_id() -> str:
    """Generate random string to use as ID."""
    return str(uuid4())


class StreamMessage(Protocol[MsgType]):
    """Generic class to represent a stream message."""

    raw_message: MsgType

    body: Union[bytes, Any]
    decoded_body: Optional["DecodedMessage"]
    headers: "AnyDict"
    path: "AnyDict"

    content_type: Optional[str]
    reply_to: str
    message_id: str
    correlation_id: str

    processed: bool
    committed: bool

    async def ack(self) -> None: ...

    async def nack(self) -> None: ...

    async def reject(self) -> None: ...


class ABCMessage(StreamMessage[MsgType]):
    """Generic class to represent a stream message."""

    decoded_body: Optional["DecodedMessage"]

    def __init__(
        self,
        *,
        raw_message: MsgType,
        body: Union[bytes, Any],
        headers: Optional["AnyDict"] = None,
        path: Optional["AnyDict"] = None,
        content_type: Optional[str] = None,
        reply_to: str = "",
        message_id: str = "",
        correlation_id: str = "",
    ):
        self.raw_message = raw_message
        self.body = body
        self.reply_to = reply_to
        self.content_type = content_type

        self.headers = headers or {}
        self.path = path or {}

        self.message_id = message_id or gen_cor_id()
        self.correlation_id = correlation_id or self.message_id

        self.decoded_body = None
        self.processed = False
        self.committed = False

    async def ack(self) -> None:
        self.committed = True

    async def nack(self) -> None:
        self.committed = True

    async def reject(self) -> None:
        self.committed = True


def decode_message(message: "StreamMessage[Any]") -> "DecodedMessage":
    """Decodes a message."""
    body: Any = getattr(message, "body", message)
    m: "DecodedMessage" = body

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
    msg: Union[Sequence["SendableMessage"], "SendableMessage"],
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
