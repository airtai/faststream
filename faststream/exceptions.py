from typing import Iterable


class FastStreamException(Exception):  # noqa: N818
    """Basic FastStream exception class."""


class SkipMessage(FastStreamException):
    """Watcher Instruction to skip message."""


class IgnoredException(FastStreamException):
    """Basic Exception class ignoring by watcher context and log middleware."""

class StopConsume(IgnoredException):
    """Raise it to stop Handler consuming."""


class StopApplication(IgnoredException, SystemExit):
    """Raise it to stop FastStream application."""


class HandlerException(FastStreamException):
    """Base Handler Exception."""


class AckMessage(HandlerException):
    """Raise it to `ack` a message immediately."""


class NackMessage(HandlerException):
    """Raise it to `nack` a message immediately."""


class RejectMessage(HandlerException):
    """Raise it to `reject` a message immediately."""


class SetupError(FastStreamException, ValueError):
    """Exception to raise at wrong method usage."""


class ValidationError(FastStreamException, ValueError):
    """Exception to raise at startup hook validation error."""

    def __init__(self, fields: Iterable[str] = ()) -> None:
        self.fields = fields


WRONG_PUBLISH_ARGS = SetupError(
    "You should use `reply_to` to send response to long-living queue "
    "and `rpc` to get response in sync mode."
)


NOT_CONNECTED_YET = "Please, `connect()` the broker first"
