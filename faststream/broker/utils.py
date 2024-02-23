import asyncio
from contextlib import suppress
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    Callable,
    Optional,
    Type,
    Union,
)

import anyio

from faststream.broker.push_back_watcher import (
    BaseWatcher,
    CounterWatcher,
    EndlessWatcher,
    OneTryWatcher,
    WatcherContext,
)
from faststream.utils.functions import fake_context

if TYPE_CHECKING:
    from logging import Logger
    from types import TracebackType

    from typing_extensions import Self


def get_watcher(
    logger: Optional["Logger"],
    try_number: Union[bool, int],
) -> BaseWatcher:
    """Get a watcher object based on the provided parameters.

    Args:
        logger: Optional logger object for logging messages.
        try_number: Optional parameter to specify the type of watcher.
            - If set to True, an EndlessWatcher object will be returned.
            - If set to False, a OneTryWatcher object will be returned.
            - If set to an integer, a CounterWatcher object with the specified maximum number of tries will be returned.

    Returns:
        A watcher object based on the provided parameters.

    """
    watcher: Optional[BaseWatcher]
    if try_number is True:
        watcher = EndlessWatcher()
    elif try_number is False:
        watcher = OneTryWatcher()
    else:
        watcher = CounterWatcher(logger=logger, max_tries=try_number)
    return watcher


def get_watcher_context(
    logger: Optional["Logger"],
    no_ack: bool,
    retry: Union[bool, int],
    **extra_options: Any,
) -> Callable[..., AsyncContextManager[None]]:
    if no_ack:
        return fake_context
    else:
        return partial(
            WatcherContext, watcher=get_watcher(logger, retry), **extra_options
        )


class MultiLock:
    """A class representing a multi lock."""

    def __init__(self) -> None:
        """Initialize a new instance of the class."""
        self.queue: "asyncio.Queue[None]" = asyncio.Queue()

    def __enter__(self) -> "Self":
        """Enter the context."""
        self.queue.put_nowait(None)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional["TracebackType"],
    ) -> None:
        """Exit the context."""
        with suppress(asyncio.QueueEmpty, ValueError):
            self.queue.get_nowait()
            self.queue.task_done()

    @property
    def qsize(self) -> int:
        """Return the size of the queue."""
        return self.queue.qsize()

    @property
    def empty(self) -> bool:
        """Return whether the queue is empty."""
        return self.queue.empty()

    async def wait_release(self, timeout: Optional[float] = None) -> None:
        """Wait for the queue to be released.

        Using for graceful shutdown.
        """
        if timeout:
            with anyio.move_on_after(timeout):
                await self.queue.join()
