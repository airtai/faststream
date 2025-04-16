from collections.abc import Iterable
from pprint import pformat
from typing import Any


class FastStreamException(Exception):  # noqa: N818
    """Basic FastStream exception class."""


class IgnoredException(FastStreamException):
    """Basic Exception class ignoring by watcher context and log middleware."""


class StopConsume(IgnoredException):
    """Raise it to stop Handler consuming."""

    def __str__(self) -> str:
        return "Consumer was stopped"


class StopApplication(IgnoredException, SystemExit):
    """Raise it to stop FastStream application."""

    def __str__(self) -> str:
        return "Application was stopped"


class HandlerException(IgnoredException):
    """Base Handler Exception."""


class SkipMessage(HandlerException):
    """Watcher Instruction to skip message."""

    def __str__(self) -> str:
        return "Message was skipped"


class AckMessage(HandlerException):
    """Exception raised to acknowledge a message immediately.

    This exception can be used to ack a message with additional options.
    To watch all allowed parameters, please take a look at your broker `message.ack(**extra_options)` method
    signature.

    Args:
        extra_options (Any): Additional parameters that will be passed to `message.ack(**extra_options)` method.
    """

    def __init__(self, **extra_options: Any) -> None:
        self.extra_options = extra_options
        super().__init__()

    def __str__(self) -> str:
        return "Message was acked"


class NackMessage(HandlerException):
    """Exception raised to negatively acknowledge a message immediately.

    This exception can be used to nack a message with additional options.
    To watch all allowed parameters, please take a look to your broker's `message.nack(**extra_options)` method
    signature.

    Args:
        kwargs (Any): Additional parameters that will be passed to `message.nack(**extra_options)` method.
    """

    def __init__(self, **kwargs: Any) -> None:
        self.extra_options = kwargs
        super().__init__()

    def __str__(self) -> str:
        return "Message was nacked"


class RejectMessage(HandlerException):
    """Exception raised to reject a message immediately.

    This exception can be used to reject a message with additional options.
    To watch all allowed parameters, please take a look to your broker's `message.reject(**extra_options)` method
    signature.

    Args:
        kwargs (Any): Additional parameters that will be passed to `message.reject(**extra_options)` method.
    """

    def __init__(self, **kwargs: Any) -> None:
        self.extra_options = kwargs
        super().__init__()

    def __str__(self) -> str:
        return "Message was rejected"


class SetupError(FastStreamException, ValueError):
    """Exception to raise at wrong method usage."""


class StartupValidationError(FastStreamException, ValueError):
    """Exception to raise at startup hook validation error."""

    def __init__(
        self,
        missed_fields: Iterable[str] = (),
        invalid_fields: Iterable[str] = (),
    ) -> None:
        self.missed_fields = missed_fields
        self.invalid_fields = invalid_fields

    def __str__(self) -> str:
        return (
            f"\n    Incorrect options `{' / '.join(f'--{i}' for i in (*self.missed_fields, *self.invalid_fields))}`"
            "\n    You registered extra options in your application `lifespan/on_startup` hook, but set them wrong in CLI."
        )


class FeatureNotSupportedException(FastStreamException, NotImplementedError):  # noqa: N818
    """Raises at planned NotImplemented operation call."""


class SubscriberNotFound(FastStreamException):
    """Raises as a service message or in tests."""


class IncorrectState(FastStreamException):
    """Raises in FSM at wrong state calling."""


class ContextError(FastStreamException, KeyError):
    """Raises if context exception occurred."""

    def __init__(self, context: Any, field: str) -> None:
        self.context = context
        self.field = field

    def __str__(self) -> str:
        return "".join(
            (
                f"\n    Key `{self.field}` not found in the context\n    ",
                pformat(self.context),
            ),
        )


WRONG_PUBLISH_ARGS = SetupError(
    "You should use `reply_to` to send response to long-living queue "
    "and `rpc` to get response in sync mode.",
)


NOT_CONNECTED_YET = "Please, `connect()` the broker first."


INSTALL_YAML = """
To generate YAML documentation, please install dependencies:\n
pip install PyYAML
"""

INSTALL_WATCHFILES = """
To use restart feature, please install dependencies:\n
pip install watchfiles
"""

SCHEMA_NOT_SUPPORTED = "`{schema_filename}` not supported. Make sure that your schema is valid and schema version supported by FastStream"
