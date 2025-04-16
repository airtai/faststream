import asyncio
import multiprocessing
import os
import signal
import sys
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from multiprocessing.context import SpawnProcess
    from types import FrameType

    from faststream._internal.basic_types import DecoratedCallableNone

multiprocessing.allow_connection_pickling()
spawn = multiprocessing.get_context("spawn")


HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)
if sys.platform == "win32":  # pragma: py-not-win32
    HANDLED_SIGNALS += (signal.SIGBREAK,)  # Windows signal 21. Sent by Ctrl+Break.


def set_exit(
    func: Callable[[int, Optional["FrameType"]], Any],
    *,
    sync: bool = False,
) -> None:
    """Set exit handler for signals.

    Args:
        func: A callable object that takes an integer and an optional frame type as arguments and returns any value.
        sync: set sync or async signal callback.
    """
    if not sync:
        with suppress(NotImplementedError):
            loop = asyncio.get_event_loop()

            for sig in HANDLED_SIGNALS:
                loop.add_signal_handler(sig, func, sig, None)

            return

    # Windows or sync mode
    for sig in HANDLED_SIGNALS:
        signal.signal(sig, func)


def get_subprocess(target: "DecoratedCallableNone", args: Any) -> "SpawnProcess":
    """Spawn a subprocess."""
    stdin_fileno: Optional[int]
    try:
        stdin_fileno = sys.stdin.fileno()
    except OSError:
        stdin_fileno = None

    return spawn.Process(
        target=subprocess_started,
        args=args,
        kwargs={"t": target, "stdin_fileno": stdin_fileno},
    )


def subprocess_started(
    *args: Any,
    t: "DecoratedCallableNone",
    stdin_fileno: Optional[int],
) -> None:
    """Start a subprocess."""
    if stdin_fileno is not None:  # pragma: no cover
        sys.stdin = os.fdopen(stdin_fileno)
    t(*args)
