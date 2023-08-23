import logging
from functools import wraps
from typing import Awaitable, Callable, Optional, Union

from propan.broker.message import PropanMessage
from propan.broker.push_back_watcher import (
    BaseWatcher,
    CounterWatcher,
    EndlessWatcher,
    OneTryWatcher,
)
from propan.broker.types import AsyncWrappedHandlerCall, MsgType, T_HandlerReturn
from propan.exceptions import HandlerException
from propan.utils import context


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


def suppress_decor(
    func: Callable[
        [PropanMessage[MsgType]],
        Awaitable[T_HandlerReturn],
    ],
) -> AsyncWrappedHandlerCall[MsgType, T_HandlerReturn]:
    @wraps(func)
    async def suppress_wrapper(
        message: PropanMessage[MsgType],
        reraise_exc: bool = False,
    ) -> Optional[T_HandlerReturn]:
        try:
            return await func(message)
        except HandlerException as e:
            raise e
        except Exception as e:
            if reraise_exc is True:
                raise e

            return None

    return suppress_wrapper


def set_message_context(
    func: Callable[
        [PropanMessage[MsgType]],
        Awaitable[T_HandlerReturn],
    ],
) -> Callable[[PropanMessage[MsgType]], Awaitable[T_HandlerReturn]]:
    @wraps(func)
    async def set_message_wrapper(message: PropanMessage[MsgType]) -> T_HandlerReturn:
        with context.scope("message", message):
            return await func(message)

    return set_message_wrapper
