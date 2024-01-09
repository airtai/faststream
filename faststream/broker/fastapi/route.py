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
    List,
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

from faststream._compat import FASTAPI_V106, raise_fastapi_validation_error
from faststream.broker.core.asynchronous import BrokerAsyncUsecase
from faststream.broker.message import StreamMessage as NativeMessage
from faststream.broker.schemas import NameRequired
from faststream.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.types import AnyDict, SendableMessage


class StreamRoute(BaseRoute, Generic[MsgType, P_HandlerParams, T_HandlerReturn]):
    """A class representing a stream route.

    Attributes:
        handler : HandlerCallWrapper object representing the handler for the route
        path : path of the route
        broker : BrokerAsyncUsecase object representing the broker for the route
        dependant : Dependable object representing the dependencies for the route
    """

    handler: HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]

    def __init__(
        self,
        path: Union[NameRequired, str, None],
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
        """Initialize a class instance.

        Args:
            path: The path of the instance.
            *extra: Additional arguments.
            endpoint: The endpoint of the instance.
            broker: The broker of the instance.
            dependencies: The dependencies of the instance.
            dependency_overrides_provider: The provider for dependency overrides.
            **handle_kwargs: Additional keyword arguments.

        Returns:
            None.
        """
        self.path = path or ""
        self.broker = broker

        path_name = self.path if isinstance(self.path, str) else self.path.name

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
    """A class to represent a stream message.

    Attributes:
        scope : dictionary representing the scope of the message
        _cookies : dictionary representing the cookies of the message
        _headers : dictionary representing the headers of the message
        _body : dictionary representing the body of the message
        _query_params : dictionary representing the query parameters of the message

    Methods:
        __init__ : initializes the StreamMessage object
        get_session : returns a callable function that handles the session of the message
    """

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
        """Initialize a class instance.

        Args:
            body: The body of the request as a dictionary.
            headers: The headers of the request as a dictionary.
            path: The path of the request as a dictionary.

        Attributes:
            scope: A dictionary to store the scope of the request.
            _cookies: A dictionary to store the cookies of the request.
            _headers: A dictionary to store the headers of the request.
            _body: A dictionary to store the body of the request.
            _query_params: A dictionary to store the query parameters of the request.

        """
        self._headers = headers
        self._body = body
        self._query_params = path

        self.scope = {"path_params": self._query_params}
        self._cookies = {}

    @classmethod
    def get_session(
        cls,
        dependant: Dependant,
        dependency_overrides_provider: Optional[Any] = None,
    ) -> Callable[[NativeMessage[Any]], Awaitable[SendableMessage]]:
        """Creates a session for handling requests.

        Args:
            dependant: The dependant object representing the session.
            dependency_overrides_provider: Optional provider for dependency overrides.

        Returns:
            A callable that takes a native message and returns an awaitable sendable message.

        Raises:
            AssertionError: If the dependant call is not defined.

        Note:
            This function is used to create a session for handling requests. It takes a dependant object, which represents the session, and a dependency overrides provider, which allows for overriding dependencies. It returns a callable that takes a native message and returns an awaitable sendable message. The session is created based on the dependant object and the message passed to the callable. The session is then used to call the function obtained from the dependant object, and the result is returned.
        """
        assert dependant.call  # nosec B101

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
            """An asynchronous function that processes an incoming message and returns a sendable message.

            Args:
                message : The incoming message to be processed

            Returns:
                The sendable message

            Raises:
                TypeError: If the body of the message is not a dictionary
            !!! note

                The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
            """
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

            return await func(session)

        return app


def get_app(
    dependant: Dependant,
    dependency_overrides_provider: Optional[Any] = None,
) -> Callable[
    [StreamMessage],
    Coroutine[Any, Any, SendableMessage],
]:
    """Creates a FastAPI application.

    Args:
        dependant: The dependant object that defines the endpoint function and its dependencies.
        dependency_overrides_provider: Optional provider for dependency overrides.

    Returns:
        The FastAPI application as a callable that takes a StreamMessage object as input and returns a SendableMessage coroutine.

    Raises:
        AssertionError: If the code reaches an unreachable state.
    """

    async def app(request: StreamMessage) -> SendableMessage:
        """Handle an HTTP request and return a response.

        Args:
            request: The incoming HTTP request.

        Returns:
            The response to be sent back to the client.

        Raises:
            AssertionError: If the code reaches an unreachable point.
        """
        async with AsyncExitStack() as stack:
            if FASTAPI_V106:
                kwargs = {"async_exit_stack": stack}
            else:
                request.scope["fastapi_astack"] = stack
                kwargs = {}

            solved_result = await solve_dependencies(
                request=request,
                body=request._body,  # type: ignore[arg-type]
                dependant=dependant,
                dependency_overrides_provider=dependency_overrides_provider,
                **kwargs,  # type: ignore[arg-type]
            )

            values, errors, _, _2, _3 = solved_result
            if errors:
                raise_fastapi_validation_error(errors, request._body)  # type: ignore[arg-type]

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
