import asyncio
import inspect
from collections.abc import Awaitable, Iterable
from contextlib import AsyncExitStack
from functools import wraps
from itertools import dropwhile
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Union,
)

from fast_depends.dependencies import Dependant
from fastapi.routing import run_endpoint_function, serialize_response
from starlette.requests import Request

from faststream._internal.context import Context
from faststream._internal.types import P_HandlerParams, T_HandlerReturn
from faststream.exceptions import SetupError
from faststream.response import Response, ensure_response

from ._compat import (
    FASTAPI_V106,
    create_response_field,
    raise_fastapi_validation_error,
    solve_faststream_dependency,
)
from .get_dependant import (
    get_fastapi_native_dependant,
    has_forbidden_types,
    is_faststream_decorated,
    mark_faststream_decorated,
)

if TYPE_CHECKING:
    from fastapi import params
    from fastapi._compat import ModelField
    from fastapi.dependencies.models import Dependant as FastAPIDependant
    from fastapi.types import IncEx

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.state import DIState
    from faststream.message import StreamMessage as NativeMessage


class StreamMessage(Request):
    """A class to represent a stream message."""

    scope: "AnyDict"
    _cookies: "AnyDict"
    _headers: "AnyDict"  # type: ignore[assignment]
    _body: Union["AnyDict", list[Any]]  # type: ignore[assignment]
    _query_params: "AnyDict"  # type: ignore[assignment]

    def __init__(
        self,
        *,
        body: Union["AnyDict", list[Any]],
        headers: "AnyDict",
        path: "AnyDict",
    ) -> None:
        """Initialize a class instance."""
        self._headers = headers
        self._body = body
        self._query_params = path

        self.scope = {"path_params": self._query_params}
        self._cookies = {}


def wrap_callable_to_fastapi_compatible(
    user_callable: Callable[P_HandlerParams, T_HandlerReturn],
    *,
    provider_factory: Callable[[], Any],
    dependencies: Iterable["params.Depends"],
    response_model: Any,
    response_model_include: Optional["IncEx"],
    response_model_exclude: Optional["IncEx"],
    response_model_by_alias: bool,
    response_model_exclude_unset: bool,
    response_model_exclude_defaults: bool,
    response_model_exclude_none: bool,
    state: "DIState",
) -> Callable[["NativeMessage[Any]"], Awaitable[Any]]:
    if has_forbidden_types(user_callable, (Dependant,)):
        msg = (
            f"Incorrect `faststream.Depends` usage at `{user_callable.__name__}`. "
            "For FastAPI integration use `fastapi.Depends` instead."
        )
        raise SetupError(msg)

    if has_forbidden_types(user_callable, (Context,)):
        msg = (
            f"Incorrect `faststream.Context` usage at `{user_callable.__name__}`. "
            "For FastAPI integration use `faststream.[broker].fastapi.Context` instead."
        )
        raise SetupError(msg)

    if is_faststream_decorated(user_callable):
        return user_callable  # type: ignore[return-value]

    if response_model:
        response_field = create_response_field(
            name="ResponseModel",
            type_=response_model,
            mode="serialization",
        )
    else:
        response_field = None

    parsed_callable = build_faststream_to_fastapi_parser(
        dependent=get_fastapi_native_dependant(user_callable, list(dependencies)),
        provider_factory=provider_factory,
        response_field=response_field,
        response_model_include=response_model_include,
        response_model_exclude=response_model_exclude,
        response_model_by_alias=response_model_by_alias,
        response_model_exclude_unset=response_model_exclude_unset,
        response_model_exclude_defaults=response_model_exclude_defaults,
        response_model_exclude_none=response_model_exclude_none,
        state=state,
    )

    mark_faststream_decorated(parsed_callable)
    return wraps(user_callable)(parsed_callable)


def build_faststream_to_fastapi_parser(
    *,
    dependent: "FastAPIDependant",
    provider_factory: Callable[[], Any],
    response_field: Optional["ModelField"],
    response_model_include: Optional["IncEx"],
    response_model_exclude: Optional["IncEx"],
    response_model_by_alias: bool,
    response_model_exclude_unset: bool,
    response_model_exclude_defaults: bool,
    response_model_exclude_none: bool,
    state: "DIState",
) -> Callable[["NativeMessage[Any]"], Awaitable[Any]]:
    """Creates a session for handling requests."""
    assert dependent.call  # nosec B101

    consume = make_fastapi_execution(
        dependent=dependent,
        provider_factory=provider_factory,
        response_field=response_field,
        response_model_include=response_model_include,
        response_model_exclude=response_model_exclude,
        response_model_by_alias=response_model_by_alias,
        response_model_exclude_unset=response_model_exclude_unset,
        response_model_exclude_defaults=response_model_exclude_defaults,
        response_model_exclude_none=response_model_exclude_none,
    )

    dependencies_names = tuple(i.name for i in dependent.dependencies)

    first_arg = next(
        dropwhile(
            lambda i: i in dependencies_names,
            inspect.signature(dependent.call).parameters,
        ),
        None,
    )

    async def parsed_consumer(message: "NativeMessage[Any]") -> Any:
        """Wrapper, that parser FastStream message to FastAPI compatible one."""
        body = await message.decode()

        fastapi_body: Union[AnyDict, list[Any]]
        if first_arg is not None:
            if isinstance(body, dict):
                path = fastapi_body = body or {}
            elif isinstance(body, list):
                fastapi_body, path = body, {}
            else:
                path = fastapi_body = {first_arg: body}

            stream_message = StreamMessage(
                body=fastapi_body,
                headers={"context__": state.context, **message.headers},
                path={**path, **message.path},
            )

        else:
            stream_message = StreamMessage(
                body={},
                headers={"context__": state.context},
                path={},
            )

        return await consume(stream_message, message)

    return parsed_consumer


def make_fastapi_execution(
    *,
    dependent: "FastAPIDependant",
    provider_factory: Callable[[], Any],
    response_field: Optional["ModelField"],
    response_model_include: Optional["IncEx"],
    response_model_exclude: Optional["IncEx"],
    response_model_by_alias: bool,
    response_model_exclude_unset: bool,
    response_model_exclude_defaults: bool,
    response_model_exclude_none: bool,
) -> Callable[
    ["StreamMessage", "NativeMessage[Any]"],
    Awaitable[Response],
]:
    """Creates a FastAPI application."""
    is_coroutine = asyncio.iscoroutinefunction(dependent.call)

    async def app(
        request: "StreamMessage",
        raw_message: "NativeMessage[Any]",  # to support BackgroundTasks by middleware
    ) -> Response:
        """Consume StreamMessage and return user function result."""
        async with AsyncExitStack() as stack:
            if FASTAPI_V106:
                kwargs = {"async_exit_stack": stack}
            else:
                request.scope["fastapi_astack"] = stack
                kwargs = {}

            solved_result = await solve_faststream_dependency(
                request=request,
                dependant=dependent,
                dependency_overrides_provider=provider_factory(),
                **kwargs,
            )

            raw_message.background = solved_result.background_tasks  # type: ignore[attr-defined]

            if solved_result.errors:
                raise_fastapi_validation_error(solved_result.errors, request._body)  # type: ignore[arg-type]

            function_result = await run_endpoint_function(
                dependant=dependent,
                values=solved_result.values,
                is_coroutine=is_coroutine,
            )

            response = ensure_response(function_result)

            response.body = await serialize_response(
                response_content=response.body,
                field=response_field,
                include=response_model_include,
                exclude=response_model_exclude,
                by_alias=response_model_by_alias,
                exclude_unset=response_model_exclude_unset,
                exclude_defaults=response_model_exclude_defaults,
                exclude_none=response_model_exclude_none,
                is_coroutine=is_coroutine,
            )

            return response

        msg = "unreachable"
        raise AssertionError(msg)

    return app
