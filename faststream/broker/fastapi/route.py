import asyncio
import inspect
from contextlib import AsyncExitStack
from functools import wraps
from itertools import dropwhile
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    List,
    Optional,
    Union,
)

from fastapi.dependencies.utils import solve_dependencies
from fastapi.routing import run_endpoint_function, serialize_response
from fastapi.utils import create_response_field
from starlette.requests import Request
from starlette.routing import BaseRoute

from faststream._compat import FASTAPI_V106, raise_fastapi_validation_error
from faststream.broker.fastapi.get_dependant import get_fastapi_native_dependant
from faststream.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper.call import HandlerCallWrapper

if TYPE_CHECKING:
    from fastapi import params
    from fastapi._compat import ModelField
    from fastapi.dependencies.models import Dependant
    from fastapi.types import IncEx

    from faststream.broker.core.usecase import BrokerUsecase
    from faststream.broker.message import StreamMessage as NativeMessage
    from faststream.broker.schemas import NameRequired
    from faststream.types import AnyDict


class StreamRoute(
    BaseRoute,  # type: ignore[misc]
    Generic[MsgType, P_HandlerParams, T_HandlerReturn],
):
    """A class representing a stream route."""

    handler: "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]"

    def __init__(
        self,
        path: Union["NameRequired", str, None],
        *extra: Any,
        provider_factory: Callable[[], Any],
        endpoint: Union[
            Callable[P_HandlerParams, T_HandlerReturn],
            "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
        ],
        broker: "BrokerUsecase[MsgType, Any]",
        dependencies: Iterable["params.Depends"],
        response_model: Any,
        response_model_include: Optional["IncEx"],
        response_model_exclude: Optional["IncEx"],
        response_model_by_alias: bool,
        response_model_exclude_unset: bool,
        response_model_exclude_defaults: bool,
        response_model_exclude_none: bool,
        **handle_kwargs: Any,
    ) -> None:
        self.path, path_name = path or "", getattr(path, "name", "")
        self.broker = broker

        if isinstance(endpoint, HandlerCallWrapper):
            orig_call = endpoint._original_call
            while hasattr(orig_call, "__consumer__"):
                orig_call = orig_call.__wrapped__  # type: ignore[attr-defined]

        else:
            orig_call = endpoint

        dependent = get_fastapi_native_dependant(
            orig_call,
            list(dependencies),
            path_name=path_name,
        )

        if response_model:
            response_field = create_response_field(
                name="ResponseModel",
                type_=response_model,
                mode="serialization",
            )
        else:
            response_field = None

        call = wraps(orig_call)(
            StreamMessage.get_consumer(
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
        )

        if isinstance(endpoint, HandlerCallWrapper):
            endpoint._original_call = call
            handler = endpoint

        else:
            handler = call

        self.handler = broker.subscriber(  # type: ignore[assignment,call-arg]
            *extra,
            dependencies=list(dependencies),
            **handle_kwargs,
        )(
            handler,  # type: ignore[arg-type]
        )


class StreamMessage(Request):  # type: ignore[misc]
    """A class to represent a stream message."""

    scope: "AnyDict"
    _cookies: "AnyDict"
    _headers: "AnyDict"  # type: ignore
    _body: Union["AnyDict", List[Any]]  # type: ignore
    _query_params: "AnyDict"  # type: ignore

    def __init__(
        self,
        *,
        body: Union["AnyDict", List[Any]],
        headers: "AnyDict",
        path: "AnyDict",
    ) -> None:
        """Initialize a class instance."""
        self._headers = headers
        self._body = body
        self._query_params = path

        self.scope = {"path_params": self._query_params}
        self._cookies = {}

    @classmethod
    def get_consumer(
        cls,
        *,
        dependent: "Dependant",
        provider_factory: Callable[[], Any],
        response_field: Optional["ModelField"],
        response_model_include: Optional["IncEx"],
        response_model_exclude: Optional["IncEx"],
        response_model_by_alias: bool,
        response_model_exclude_unset: bool,
        response_model_exclude_defaults: bool,
        response_model_exclude_none: bool,
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

        async def real_consumer(message: "NativeMessage[Any]") -> Any:
            """An asynchronous function that processes an incoming message and returns a sendable message."""
            body = message.decoded_body

            fastapi_body: Union["AnyDict", List[Any]]
            if first_arg is not None:
                if isinstance(body, dict):
                    path = fastapi_body = body or {}
                elif isinstance(body, list):
                    fastapi_body, path = body, {}
                else:
                    path = fastapi_body = {first_arg: body}

                stream_message = cls(
                    body=fastapi_body,
                    headers=message.headers,
                    path={**path, **message.path},
                )

            else:
                stream_message = cls(
                    body={},
                    headers={},
                    path={},
                )

            return await consume(stream_message, message)

        real_consumer.__consumer__ = True  # type: ignore[attr-defined]
        return real_consumer


def make_fastapi_execution(
    *,
    dependent: "Dependant",
    provider_factory: Callable[[], Any],
    response_field: Optional["ModelField"],
    response_model_include: Optional["IncEx"],
    response_model_exclude: Optional["IncEx"],
    response_model_by_alias: bool,
    response_model_exclude_unset: bool,
    response_model_exclude_defaults: bool,
    response_model_exclude_none: bool,
) -> Callable[
    [StreamMessage, "NativeMessage[Any]"],
    Awaitable[Any],
]:
    """Creates a FastAPI application."""
    is_coroutine = asyncio.iscoroutinefunction(dependent.call)

    async def app(
        request: StreamMessage,
        raw_message: "NativeMessage[Any]",
    ) -> Any:
        """Consume StreamMessage and return user function result."""
        async with AsyncExitStack() as stack:
            if FASTAPI_V106:
                kwargs = {"async_exit_stack": stack}
            else:
                request.scope["fastapi_astack"] = stack
                kwargs = {}

            solved_result = await solve_dependencies(
                request=request,
                body=request._body,  # type: ignore[arg-type]
                dependant=dependent,
                dependency_overrides_provider=provider_factory(),
                **kwargs,  # type: ignore[arg-type]
            )

            values, errors, raw_message.background, _, _2 = solved_result  # type: ignore[attr-defined]

            if errors:
                raise_fastapi_validation_error(errors, request._body)  # type: ignore[arg-type]

            raw_reponse = await run_endpoint_function(
                dependant=dependent,
                values=values,
                is_coroutine=is_coroutine,
            )

            content = await serialize_response(
                response_content=raw_reponse,
                field=response_field,
                include=response_model_include,
                exclude=response_model_exclude,
                by_alias=response_model_by_alias,
                exclude_unset=response_model_exclude_unset,
                exclude_defaults=response_model_exclude_defaults,
                exclude_none=response_model_exclude_none,
                is_coroutine=is_coroutine,
            )

            return content

        return None

    return app
