import multiprocessing
import os
import signal
import sys
from multiprocessing.context import SpawnProcess
from types import FrameType
from typing import Any, Callable, Optional

from faststream.types import DecoratedCallableNone

multiprocessing.allow_connection_pickling()
spawn = multiprocessing.get_context("spawn")


HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


def set_exit(func: Callable[[int, Optional[FrameType]], Any]) -> None:
    for sig in HANDLED_SIGNALS:
        signal.signal(sig, func)


def get_subprocess(target: DecoratedCallableNone, args: Any) -> SpawnProcess:
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
    t: DecoratedCallableNone,
    stdin_fileno: Optional[int],
) -> None:
    if stdin_fileno is not None:  # pragma: no cover
        sys.stdin = os.fdopen(stdin_fileno)
    t(*args)
