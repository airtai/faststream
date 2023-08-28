import logging
from functools import wraps
from typing import Awaitable, Callable, Optional, Union

from faststream.broker.message import StreamMessage
from faststream.broker.push_back_watcher import (
    BaseWatcher,
    CounterWatcher,
    EndlessWatcher,
    OneTryWatcher,
)
from faststream.broker.types import MsgType, T_HandlerReturn, WrappedReturn
from faststream.utils import context


def change_logger_handlers(logger: logging.Logger, fmt: str) -> None:
    for handler in logger.handlers:
        formatter = handler.formatter
        if formatter is not None:
            use_colors = getattr(formatter, "use_colors", None)
            if use_colors is not None:
                kwargs = {"use_colors": use_colors}
            else:
                kwargs = {}
            handler.setFormatter(type(formatter)(fmt, **kwargs))


def get_watcher(
    logger: Optional[logging.Logger],
    try_number: Union[bool, int] = True,
) -> BaseWatcher:
    watcher: Optional[BaseWatcher]
    if try_number is True:
        watcher = EndlessWatcher()
    elif try_number is False:
        watcher = OneTryWatcher()
    else:
        watcher = CounterWatcher(logger=logger, max_tries=try_number)
    return watcher


def set_message_context(
    func: Callable[
        [StreamMessage[MsgType]],
        Awaitable[WrappedReturn[T_HandlerReturn]],
    ],
) -> Callable[[StreamMessage[MsgType]], Awaitable[WrappedReturn[T_HandlerReturn]]]:
    @wraps(func)
    async def set_message_wrapper(
        message: StreamMessage[MsgType],
    ) -> WrappedReturn[T_HandlerReturn]:
        with context.scope("message", message):
            return await func(message)

    return set_message_wrapper
