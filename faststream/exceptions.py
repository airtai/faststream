class SkipMessage(Exception):  # noqa: N818
    """Watcher Instruction to skip message."""


class StopConsume(Exception):  # noqa: N818
    """Raise it to stop Handler consuming."""


class HandlerException(Exception):  # noqa: N818
    """Base Handler Exception."""


class AckMessage(HandlerException):
    """Raise it to `ack` a message immediately."""


class NackMessage(HandlerException):
    """Raise it to `nack` a message immediately."""


class RejectMessage(HandlerException):
    """Raise it to `reject` a message immediately."""


WRONG_PUBLISH_ARGS = ValueError(
    "You should use `reply_to` to send response to long-living queue "
    "and `rpc` to get response in sync mode."
)


NOT_CONNECTED_YET = "Please, `connect()` the broker first"
