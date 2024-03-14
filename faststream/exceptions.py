from typing import Iterable

class FastStreamException(Exception):  # noqa: N818
    """Basic FastStream exception class."""

class SkipMessage(FastStreamException):  # noqa: N818
    """Watcher Instruction to skip message."""


class StopConsume(FastStreamException):  # noqa: N818
    """Raise it to stop Handler consuming."""


class HandlerException(FastStreamException):  # noqa: N818
    """Base Handler Exception."""


class AckMessage(HandlerException):
    """Raise it to `ack` a message immediately."""


class NackMessage(HandlerException):
    """Raise it to `nack` a message immediately."""


class RejectMessage(HandlerException):
    """Raise it to `reject` a message immediately."""


class SetupException(FastStreamException, ValueError):
    """Exception to raise at wrong method usage."""


class ValidationError(FastStreamException, ValueError):
    """Exception to raise at startup hook validation error."""

    def __init__(self, fields: Iterable[str] = ()) -> None:
        self.fields = fields


WRONG_PUBLISH_ARGS = SetupException(
    "You should use `reply_to` to send response to long-living queue "
    "and `rpc` to get response in sync mode."
)


NOT_CONNECTED_YET = "Please, `connect()` the broker first"
