import json
from contextlib import suppress
from dataclasses import dataclass, field
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
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


@dataclass
class StreamMessage(Generic[MsgType]):
    """Generic class to represent a stream message."""

    raw_message: "MsgType"

    body: Union[bytes, Any]
    headers: "AnyDict" = field(default_factory=dict)
    batch_headers: List["AnyDict"] = field(default_factory=list)
    path: "AnyDict" = field(default_factory=dict)

    content_type: Optional[str] = None
    reply_to: str = ""
    message_id: str = field(default_factory=gen_cor_id)  # pragma: no cover
    correlation_id: str = field(
        default_factory=gen_cor_id  # pragma: no cover
    )

    decoded_body: Optional["DecodedMessage"] = field(default=None, init=False)
    processed: bool = field(default=False, init=False)
    committed: bool = field(default=False, init=False)

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

    if (
        content_type := getattr(message, "content_type", Parameter.empty)
    ) is not Parameter.empty:
        content_type = cast(Optional[str], content_type)

        if not content_type:
            with suppress(json.JSONDecodeError, UnicodeDecodeError):
                m = json_loads(body)

        elif ContentTypes.text.value in content_type:
            m = body.decode()

        elif ContentTypes.json.value in content_type:
            m = json_loads(body)

    else:
        with suppress(json.JSONDecodeError, UnicodeDecodeError):
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
