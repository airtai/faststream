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
    Coroutine,
    Generic,
    Iterable,
    List,
    Optional,
    Union,
)

from fastapi import params
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import (
    get_dependant,
    get_parameterless_sub_dependant,
    solve_dependencies,
)
from fastapi.routing import run_endpoint_function, serialize_response
from fastapi.utils import create_response_field
from starlette.requests import Request
from starlette.routing import BaseRoute

from faststream._compat import FASTAPI_V106, PYDANTIC_V2, raise_fastapi_validation_error
from faststream.broker.core.broker import BrokerUsecase
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.message import StreamMessage as NativeMessage
from faststream.broker.schemas import NameRequired
from faststream.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from faststream.types import AnyDict, SendableMessage

if TYPE_CHECKING:
    from fastapi._compat import ModelField
    from fastapi.types import IncEx


class StreamRoute(BaseRoute, Generic[MsgType, P_HandlerParams, T_HandlerReturn]):
    """A class representing a stream route.

    Attributes:
        handler : HandlerCallWrapper object representing the handler for the route
        path : path of the route
        broker : BrokerUsecase object representing the broker for the route
        dependent : Dependable object representing the dependencies for the route
    """

    handler: HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]

    def __init__(
        self,
        path: Union[NameRequired, str, None],
        *extra: Union[NameRequired, str],
        provider_factory: Callable[[], Any],
        endpoint: Union[
            Callable[P_HandlerParams, T_HandlerReturn],
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        ],
        broker: BrokerUsecase[MsgType, Any],
        dependencies: Iterable[params.Depends],
        response_model: Any,
        response_model_include: Optional["IncEx"],
        response_model_exclude: Optional["IncEx"],
        response_model_by_alias: bool,
        response_model_exclude_unset: bool,
        response_model_exclude_defaults: bool,
        response_model_exclude_none: bool,
        **handle_kwargs: Any,
    ) -> None:
        self.path = path or ""
        self.broker = broker

        path_name = self.path if isinstance(self.path, str) else self.path.name

        if isinstance(endpoint, HandlerCallWrapper):
            orig_call = endpoint._original_call
        else:
            orig_call = endpoint

        dependent = get_dependant(
            path=path_name,
            call=orig_call,
        )
        for depends in list(dependencies)[::-1]:
            dependent.dependencies.insert(
                0,
                get_parameterless_sub_dependant(depends=depends, path=path_name),
            )
        dependent = _patch_fastapi_dependent(dependent)

        self.dependent = dependent

        if response_model:
            response_field = create_response_field(
                name="ResponseModel",
                type_=response_model,
                mode="serialization",
            )
        else:
            response_field = None

        call = wraps(orig_call)(
            StreamMessage.get_session(
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

        self.handler = broker.subscriber(
            *extra,
            get_dependent=lambda *_: dependent,
            **handle_kwargs,
        )(
            handler  # type: ignore[arg-type]
        )


class StreamMessage(Request):
    """A class to represent a stream message."""

    scope: AnyDict
    _cookies: AnyDict
    _headers: AnyDict  # type: ignore
    _body: Union[AnyDict, List[Any]]  # type: ignore
    _query_params: AnyDict  # type: ignore

    def __init__(
        self,
        *,
        body: Union[AnyDict, List[Any]],
        headers: AnyDict,
        path: AnyDict,
    ) -> None:
        """Initialize a class instance."""
        self._headers = headers
        self._body = body
        self._query_params = path

        self.scope = {"path_params": self._query_params}
        self._cookies = {}

    @classmethod
    def get_session(
        cls,
        *,
        dependent: Dependant,
        provider_factory: Callable[[], Any],
        response_field: Optional["ModelField"],
        response_model_include: Optional["IncEx"],
        response_model_exclude: Optional["IncEx"],
        response_model_by_alias: bool,
        response_model_exclude_unset: bool,
        response_model_exclude_defaults: bool,
        response_model_exclude_none: bool,
    ) -> Callable[[NativeMessage[Any]], Awaitable[SendableMessage]]:
        """Creates a session for handling requests."""
        assert dependent.call  # nosec B101

        consume = make_fastapi_consumer(
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

        async def app(message: NativeMessage[Any]) -> SendableMessage:
            """An asynchronous function that processes an incoming message and returns a sendable message."""
            body = message.decoded_body

            fastapi_body: Union[AnyDict, List[Any]]
            if first_arg is not None:
                if isinstance(body, dict):
                    path = fastapi_body = body or {}
                elif isinstance(body, list):
                    fastapi_body, path = body, {}
                else:
                    path = fastapi_body = {first_arg: body}

                session = cls(
                    body=fastapi_body,
                    headers=message.headers,
                    path={**path, **message.path},
                )

            else:
                session = cls(
                    body={},
                    headers={},
                    path={},
                )

            return await consume(session)

        return app


def make_fastapi_consumer(
    *,
    dependent: Dependant,
    provider_factory: Callable[[], Any],
    response_field: Optional["ModelField"],
    response_model_include: Optional["IncEx"],
    response_model_exclude: Optional["IncEx"],
    response_model_by_alias: bool,
    response_model_exclude_unset: bool,
    response_model_exclude_defaults: bool,
    response_model_exclude_none: bool,
) -> Callable[
    [StreamMessage],
    Coroutine[Any, Any, SendableMessage],
]:
    """Creates a FastAPI application."""
    is_coroutine = asyncio.iscoroutinefunction(dependent.call)

    async def app(request: StreamMessage) -> SendableMessage:
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

            values, errors, background_tasks, _, _2 = solved_result

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

            # TODO: run backgrounds somewhere
            # if background_tasks:
            #     await background_tasks()

            return content

        return None

    return app


def _patch_fastapi_dependent(dependent: Dependant) -> Dependant:
    """Patch FastAPI by adding fields for AsyncAPI schema generation."""
    from pydantic import create_model  # FastAPI always has pydantic

    params = dependent.query_params + dependent.body_params  # type: ignore[attr-defined]

    for d in dependent.dependencies:
        params.extend(d.query_params + d.body_params)  # type: ignore[attr-defined]

    params_unique = {}
    params_names = set()
    for p in params:
        if p.name not in params_names:
            params_names.add(p.name)
            info = p.field_info if PYDANTIC_V2 else p
            params_unique[p.name] = (info.annotation, info.default)  # type: ignore[attr-defined]

    dependent.model = create_model(  # type: ignore[attr-defined,call-overload]
        getattr(dependent.call, "__name__", type(dependent.call).__name__),
        **params_unique,
    )
    dependent.custom_fields = {}  # type: ignore[attr-defined]
    dependent.flat_params = params_unique  # type: ignore[attr-defined,assignment,misc]

    return dependent
