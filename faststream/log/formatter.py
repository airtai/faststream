import logging
import sys
from collections import defaultdict
from types import TracebackType
from typing import Callable, DefaultDict, Literal, Mapping, Optional, Tuple, Type, Union

import click

from faststream.utils.context.repository import context

original_makeRecord = logging.Logger.makeRecord  # noqa: N816


class ColourizedFormatter(logging.Formatter):
    """A class to format log messages with colorized level names.

    Attributes:
        level_name_colors : A dictionary mapping log level names to functions that colorize the level names.

    Methods:
        __init__ : Initialize the formatter with specified format strings.
        color_level_name : Colorize the level name based on the log level.
        formatMessage : Format the log record message with colorized level name.

    """

    level_name_colors: DefaultDict[str, Callable[[str], str]] = defaultdict(  # noqa: RUF012
        lambda: str,
        **{
            str(logging.DEBUG): lambda level_name: click.style(
                str(level_name), fg="cyan"
            ),
            str(logging.INFO): lambda level_name: click.style(
                str(level_name), fg="green"
            ),
            str(logging.WARNING): lambda level_name: click.style(
                str(level_name), fg="yellow"
            ),
            str(logging.ERROR): lambda level_name: click.style(
                str(level_name), fg="red"
            ),
            str(logging.CRITICAL): lambda level_name: click.style(
                str(level_name), fg="bright_red"
            ),
        },
    )

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: Optional[bool] = None,
    ) -> None:
        """Initialize the formatter with specified format strings.

        Initialize the formatter either with the specified format string, or a
        default as described above. Allow for specialized date formatting with
        the optional datefmt argument. If datefmt is omitted, you get an
        ISO8601-like (or RFC 3339-like) format.

        Use a style parameter of '%', '{' or '$' to specify that you want to
        use one of %-formatting, :meth:`str.format` (``{}``) formatting or
        :class:`string.Template` formatting in your format string.
        """
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        """Returns the colored level name.

        Args:
            level_name: The name of the level.
            level_no: The number of the level.

        Returns:
            The colored level name.

        Raises:
            KeyError: If the level number is not found in the level name colors dictionary.

        """
        return self.level_name_colors[str(level_no)](level_name)

    def formatMessage(self, record: logging.LogRecord) -> str:  # noqa: N802
        """Formats the log message.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message.

        """
        levelname = expand_log_field(record.levelname, 8)
        if self.use_colors is True:  # pragma: no cover
            levelname = self.color_level_name(levelname, record.levelno)
        record.__dict__["levelname"] = levelname
        return super().formatMessage(record)


def make_record_with_extra(
    self: logging.Logger,
    name: str,
    level: int,
    fn: str,
    lno: int,
    msg: str,
    args: Tuple[str],
    exc_info: Optional[
        Union[
            Tuple[Type[BaseException], BaseException, Optional[TracebackType]],
            Tuple[None, None, None],
        ]
    ],
    func: Optional[str] = None,
    extra: Optional[Mapping[str, object]] = None,
    sinfo: Optional[str] = None,
) -> logging.LogRecord:
    """Creates a log record with additional information.

    Args:
        self: The logger object.
        name: The name of the logger.
        level: The logging level.
        fn: The filename where the log message originated.
        lno: The line number where the log message originated.
        msg: The log message.
        args: The arguments for the log message.
        exc_info: Information about an exception.
        func: The name of the function where the log message originated.
        extra: Additional information to include in the log record.
        sinfo: Stack information.

    Returns:
        The log record.

    Note:
        If `extra` is `None`, it will be set to the value of `context.get_local("log_context")`.

    """
    if extra is None:
        extra = context.get_local(key="log_context") or context.get(
            "default_log_context"
        )

    record = original_makeRecord(
        self,
        name,
        level,
        fn,
        lno,
        msg,
        args,
        exc_info,
        func,
        extra,
        sinfo,
    )

    return record


def expand_log_field(field: str, symbols: int) -> str:
    """Expands a log field by adding spaces.

    Args:
        field: The log field to expand.
        symbols: The desired length of the expanded field.

    Returns:
        The expanded log field.

    """
    return field + (" " * (symbols - len(field)))


logging.Logger.makeRecord = make_record_with_extra  # type: ignore
