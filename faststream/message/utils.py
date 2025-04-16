import json
from collections.abc import Sequence
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Union,
    cast,
)
from uuid import uuid4

from faststream._internal._compat import dump_json, json_loads
from faststream._internal.constants import ContentTypes

if TYPE_CHECKING:
    from faststream._internal.basic_types import DecodedMessage, SendableMessage

    from .message import StreamMessage


def gen_cor_id() -> str:
    """Generate random string to use as ID."""
    return str(uuid4())


def decode_message(message: "StreamMessage[Any]") -> "DecodedMessage":
    """Decodes a message."""
    body: Any = getattr(message, "body", message)
    m: DecodedMessage = body

    if content_type := getattr(message, "content_type", False):
        content_type = ContentTypes(cast("str", content_type))

        if content_type is ContentTypes.TEXT:
            m = body.decode()

        elif content_type is ContentTypes.JSON:
            m = json_loads(body)

    else:
        # content-type not set
        with suppress(json.JSONDecodeError, UnicodeDecodeError):
            m = json_loads(body)

    return m


def encode_message(
    msg: Union[Sequence["SendableMessage"], "SendableMessage"],
) -> tuple[bytes, Optional[str]]:
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
            ContentTypes.TEXT.value,
        )

    return (
        dump_json(msg),
        ContentTypes.JSON.value,
    )
