import asyncio
import inspect
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
    cast,
)

import anyio
from typing_extensions import Self

from faststream.broker.acknowledgement_watcher import WatcherContext, get_watcher
from faststream.utils.functions import fake_context, to_async

if TYPE_CHECKING:
    from types import TracebackType

    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        AsyncCallable,
        CustomCallable,
        SyncCallable,
    )
    from faststream.types import LoggerProto


async def default_filter(msg: "StreamMessage[Any]") -> bool:
    """A function to filter stream messages."""
    return not msg.processed


def get_watcher_context(
    logger: Optional["LoggerProto"],
    no_ack: bool,
    retry: Union[bool, int],
    **extra_options: Any,
) -> Callable[..., AsyncContextManager[None]]:
    """Create Acknowledgement scope."""
    if no_ack:
        return fake_context

    else:
        return partial(
            WatcherContext,
            watcher=get_watcher(logger, retry),
            logger=logger,
            **extra_options,
        )


class MultiLock:
    """A class representing a multi lock."""

    def __init__(self) -> None:
        """Initialize a new instance of the class."""
        self.queue: "asyncio.Queue[None]" = asyncio.Queue()

    def __enter__(self) -> Self:
        """Enter the context."""
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional["TracebackType"],
    ) -> None:
        """Exit the context."""
        self.release()

    def acquire(self) -> None:
        """Acquire lock."""
        self.queue.put_nowait(None)

    def release(self) -> None:
        """Release lock."""
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


def resolve_custom_func(
    custom_func: Optional["CustomCallable"],
    default_func: "AsyncCallable",
) -> "AsyncCallable":
    """Resolve a custom parser/decoder with default one."""
    if custom_func is None:
        return default_func

    original_params = inspect.signature(custom_func).parameters

    if len(original_params) == 1:
        return to_async(cast(Union["SyncCallable", "AsyncCallable"], custom_func))

    else:
        name = tuple(original_params.items())[1][0]
        return partial(to_async(custom_func), **{name: default_func})  # type: ignore
