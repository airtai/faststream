from abc import abstractmethod
from contextlib import AsyncExitStack
from inspect import unwrap
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    List,
    Optional,
    Tuple,
)
from unittest.mock import MagicMock

from fast_depends._compat import create_model, get_config_base
from fast_depends.core import CallModel, build_call_model
from typing_extensions import Annotated, Doc

from faststream.asyncapi.base import AsyncAPIOperation
from faststream.asyncapi.message import get_response_schema
from faststream.asyncapi.utils import to_camelcase
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from faststream.types import AnyDict, SendableMessage

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware


class FakePublisher:
    """A class to represent a fake publisher."""

    def __init__(
        self,
        method: Callable[..., Awaitable[SendableMessage]],
        middlewares: Iterable["PublisherMiddleware"] = (),
        **publish_kwargs: Any,
    ) -> None:
        """Initialize an object."""
        self.method = method
        self.publish_kwargs = publish_kwargs
        self.middlewares = middlewares

    async def publish(
        self,
        message: SendableMessage,
        *args: Any,
        correlation_id: Optional[str] = None,
        extra_middlewares: Iterable["PublisherMiddleware"] = (),
        **kwargs: Any,
    ) -> Any:
        """Publish a message.

        Args:
            message: The message to be published.
            *args: Additional positional arguments.
            correlation_id: Optional correlation ID for the message.
            **kwargs: Additional keyword arguments.

        Returns:
            The published message.
        """
        publish_kwargs = self.publish_kwargs | kwargs

        async with AsyncExitStack() as stack:
            for m in chain(extra_middlewares, self.middlewares):
                message = await stack.enter_async_context(
                    m(message, *args, correlation_id=correlation_id, **publish_kwargs)
                )

            return await self.method(
                message,
                *args,
                correlation_id=correlation_id,
                **publish_kwargs,
            )


class BasePublisher(AsyncAPIOperation, Generic[MsgType]):
    """A base class for publishers in an asynchronous API."""

    calls: List[Callable[..., Any]]
    mock: Optional[MagicMock]

    def __init__(
        self,
        *,
        middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Publisher middlewares."),
        ],
        # AsyncAPI options
        schema_: Annotated[
            Optional[Any],
            Doc(
                "AsyncAPI publishing message type"
                "Should be any python-native object annotation or `pydantic.BaseModel`."
            ),
        ],
        title_: Annotated[
            Optional[str],
            Doc("AsyncAPI object title."),
        ],
        description_: Annotated[
            Optional[str],
            Doc("AsyncAPI object description."),
        ],
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ],
    ) -> None:
        """Initialize Publisher object."""
        self.schema_ = schema_
        self.middlewares = middlewares

        self.calls = []
        self._fake_handler = False
        self.mock = None

        # AsyncAPI
        self.title_=title_
        self.description_=description_
        self.include_in_schema=include_in_schema

    def set_test(
        self,
        *,
        mock: Annotated[MagicMock, Doc("Mock object to check in tests.")],
        with_fake: Annotated[
            bool, Doc("Whetevet publisher's fake subscriber created or not.")
        ],
    ) -> None:
        """Turn publisher to testing mode."""
        self.mock = mock
        self._fake_handler = with_fake

    def reset_test(self) -> None:
        """Turn off publisher's testing mode."""
        self._fake_handler = False
        self.mock = None

    def __call__(
        self,
        func: Callable[P_HandlerParams, T_HandlerReturn],
    ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
        """Decorate user's function by current publisher."""
        handler_call = HandlerCallWrapper[
            MsgType,
            P_HandlerParams,
            T_HandlerReturn,
        ](func)
        handler_call._publishers.append(self)
        self.calls.append(handler_call._original_call)
        return handler_call

    @abstractmethod
    async def publish(
        self,
        message: Any,
        *args: Any,
        correlation_id: Optional[str] = None,
        extra_middlewares: Iterable["PublisherMiddleware"] = (),
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def __hash__(self) -> int:
        raise NotImplementedError()

    def get_payloads(self) -> List[Tuple[AnyDict, str]]:
        payloads: List[Tuple[AnyDict, str]] = []

        if self.schema_:
            params = {"response__": (self.schema_, ...)}

            call_model: CallModel[Any, Any] = CallModel(
                call=lambda: None,
                model=create_model("Fake"),
                response_model=create_model(  # type: ignore[call-overload]
                    "",
                    __config__=get_config_base(),  # type: ignore[arg-type]
                    **params,  # type: ignore[arg-type]
                ),
                params=params,
            )

            body = get_response_schema(
                call_model,
                prefix=f"{self.name}:Message",
            )
            if body:  # pragma: no branch
                payloads.append((body, ""))

        else:
            for call in self.calls:
                call_model = build_call_model(call)
                body = get_response_schema(
                    call_model,
                    prefix=f"{self.name}:Message",
                )
                if body:
                    payloads.append((body, to_camelcase(unwrap(call).__name__)))

        return payloads
