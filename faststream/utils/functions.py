from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    ContextManager,
    Iterator,
    Optional,
    Union,
    overload,
)

import anyio
from fast_depends.core import CallModel
from fast_depends.utils import run_async as call_or_await

from faststream.types import F_Return, F_Spec

__all__ = (
    "call_or_await",
    "drop_response_type",
    "fake_context",
    "timeout_scope",
    "to_async",
)


@overload
def to_async(
    func: Callable[F_Spec, Awaitable[F_Return]],
) -> Callable[F_Spec, Awaitable[F_Return]]: ...


@overload
def to_async(
    func: Callable[F_Spec, F_Return],
) -> Callable[F_Spec, Awaitable[F_Return]]: ...


def to_async(
    func: Union[
        Callable[F_Spec, F_Return],
        Callable[F_Spec, Awaitable[F_Return]],
    ],
) -> Callable[F_Spec, Awaitable[F_Return]]:
    """Converts a synchronous function to an asynchronous function."""

    @wraps(func)
    async def to_async_wrapper(*args: F_Spec.args, **kwargs: F_Spec.kwargs) -> F_Return:
        """Wraps a function to make it asynchronous."""
        return await call_or_await(func, *args, **kwargs)

    return to_async_wrapper


def timeout_scope(
    timeout: Optional[float] = 30,
    raise_timeout: bool = False,
) -> ContextManager[anyio.CancelScope]:
    scope: Callable[[Optional[float]], ContextManager[anyio.CancelScope]]
    scope = anyio.fail_after if raise_timeout else anyio.move_on_after

    return scope(timeout)


@asynccontextmanager
async def fake_context(*args: Any, **kwargs: Any) -> AsyncIterator[None]:
    yield None


@contextmanager
def sync_fake_context(*args: Any, **kwargs: Any) -> Iterator[None]:
    yield None


def drop_response_type(
    model: CallModel[F_Spec, F_Return],
) -> CallModel[F_Spec, F_Return]:
    model.response_model = None
    return model


async def return_input(x: Any) -> Any:
    return x
