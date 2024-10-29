from collections.abc import AsyncIterator, Awaitable, Iterator
from contextlib import AbstractContextManager, asynccontextmanager, contextmanager
from functools import wraps
from typing import (
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
    overload,
)

import anyio
from fast_depends.core import CallModel
from fast_depends.utils import run_async as call_or_await
from typing_extensions import ParamSpec

from faststream._internal.basic_types import F_Return, F_Spec

__all__ = (
    "call_or_await",
    "drop_response_type",
    "fake_context",
    "timeout_scope",
    "to_async",
)

P = ParamSpec("P")
T = TypeVar("T")


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
) -> AbstractContextManager[anyio.CancelScope]:
    scope: Callable[[Optional[float]], AbstractContextManager[anyio.CancelScope]]
    scope = anyio.fail_after if raise_timeout else anyio.move_on_after

    return scope(timeout)


@asynccontextmanager
async def fake_context(*args: Any, **kwargs: Any) -> AsyncIterator[None]:
    yield None


@contextmanager
def sync_fake_context(*args: Any, **kwargs: Any) -> Iterator[None]:
    yield None


def drop_response_type(model: CallModel) -> CallModel:
    model.serializer.response_callback = None
    return model


async def return_input(x: Any) -> Any:
    return x
