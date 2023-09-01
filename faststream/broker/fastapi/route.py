import asyncio
import inspect
from contextlib import AsyncExitStack
from functools import wraps
from itertools import dropwhile
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Generic,
    Optional,
    Sequence,
    Union,
    cast,
)

from fastapi import params
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import (
    get_dependant,
    get_parameterless_sub_dependant,
    solve_dependencies,
)
from fastapi.routing import run_endpoint_function
from starlette.requests import Request
from starlette.routing import BaseRoute

from faststream._compat import raise_fastapi_validation_error
from faststream.broker.core.asyncronous import BrokerAsyncUsecase
from faststream.broker.message import StreamMessage as NativeMessage
from faststream.broker.schemas import NameRequired
from faststream.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.types import AnyDict, SendableMessage


class StreamRoute(BaseRoute, Generic[MsgType, P_HandlerParams, T_HandlerReturn]):
    handler: HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]

    def __init__(
        self,
        path: Union[NameRequired, str],
        *extra: Union[NameRequired, str],
        endpoint: Union[
            Callable[P_HandlerParams, T_HandlerReturn],
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        ],
        broker: BrokerAsyncUsecase[MsgType, Any],
        dependencies: Sequence[params.Depends] = (),
        dependency_overrides_provider: Optional[Any] = None,
        **handle_kwargs: Any,
    ) -> None:
        self.path = path
        self.broker = broker

        path_name = (path if isinstance(path, str) else path.name) or ""

        if isinstance(endpoint, HandlerCallWrapper):
            orig_call = endpoint._original_call
        else:
            orig_call = endpoint

        dependant = get_dependant(
            path=path_name,
            call=orig_call,
        )
        for depends in dependencies[::-1]:
            dependant.dependencies.insert(
                0,
                get_parameterless_sub_dependant(depends=depends, path=path_name),
            )
        self.dependant = dependant

        call = wraps(orig_call)(
            StreamMessage.get_session(
                dependant,
                dependency_overrides_provider,
            )
        )

        if isinstance(endpoint, HandlerCallWrapper):
            endpoint._original_call = call
            handler = endpoint

        else:
            handler = call

        self.handler = broker.subscriber(
            path,
            *extra,
            _raw=True,
            _get_dependant=lambda call: dependant,
            **handle_kwargs,
        )(
            handler  # type: ignore[arg-type]
        )


class StreamMessage(Request):
    scope: AnyDict
    _cookies: AnyDict
    _headers: AnyDict  # type: ignore
    _body: AnyDict  # type: ignore
    _query_params: AnyDict  # type: ignore

    def __init__(
        self,
        body: Optional[AnyDict] = None,
        headers: Optional[AnyDict] = None,
    ):
        self.scope = {}
        self._cookies = {}
        self._headers = headers or {}
        self._body = body or {}
        self._query_params = self._body

    @classmethod
    def get_session(
        cls,
        dependant: Dependant,
        dependency_overrides_provider: Optional[Any] = None,
    ) -> Callable[[NativeMessage[Any]], Awaitable[SendableMessage]]:
        if dependant.call is None:
            raise RuntimeError()

        func = get_app(dependant, dependency_overrides_provider)

        dependencies_names = tuple(i.name for i in dependant.dependencies)

        first_arg = next(
            dropwhile(
                lambda i: i in dependencies_names,
                inspect.signature(dependant.call).parameters,
            ),
            None,
        )

        async def app(message: NativeMessage[Any]) -> SendableMessage:
            body = message.decoded_body
            if first_arg is not None:
                if not isinstance(body, dict):  # pragma: no branch
                    fastapi_body: AnyDict = {first_arg: body}
                else:
                    fastapi_body = body

                session = cls(fastapi_body, message.headers)
            else:
                session = cls()
            return await func(session)

        return app


def get_app(
    dependant: Dependant,
    dependency_overrides_provider: Optional[Any] = None,
) -> Callable[[StreamMessage], Coroutine[Any, Any, SendableMessage]]:
    async def app(request: StreamMessage) -> SendableMessage:
        async with AsyncExitStack() as stack:
            request.scope["fastapi_astack"] = stack

            solved_result = await solve_dependencies(
                request=request,
                body=request._body,
                dependant=dependant,
                dependency_overrides_provider=dependency_overrides_provider,
            )

            values, errors, _, _2, _3 = solved_result
            if errors:
                raise_fastapi_validation_error(errors, request._body)

            return cast(
                SendableMessage,
                await run_endpoint_function(
                    dependant=dependant,
                    values=values,
                    is_coroutine=asyncio.iscoroutinefunction(dependant.call),
                ),
            )

        raise AssertionError("unreachable")

    return app
