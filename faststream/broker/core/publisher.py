from abc import abstractmethod, abstractproperty
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
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

from faststream.asyncapi.base import AsyncAPIOperation
from faststream.asyncapi.message import get_response_schema
from faststream.asyncapi.utils import to_camelcase
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from faststream.types import AnyDict, SendableMessage

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware


class FakePublisher:
    """A class to represent a fake publisher.

    Attributes:
        method : a callable method that takes arguments and returns an awaitable sendable message

    Methods:
        publish : asynchronously publishes a message with optional correlation ID and additional keyword arguments
    """

    def __init__(
        self,
        method: Callable[..., Awaitable[SendableMessage]],
        middlewares: Iterable["PublisherMiddleware"] = (),
        **publish_kwargs: Any,
    ) -> None:
        """Initialize an object.

        Args:
            method: A callable that takes any number of arguments and returns an awaitable sendable message.
        """
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
            *args: Additinal positional arguments.
            correlation_id: Optional correlation ID for the message.
            **kwargs: Additional keyword arguments.

        Returns:
            The published message.
        """
        kwargs.update(self.publish_kwargs)

        async with AsyncExitStack() as stack:
            for m in chain(extra_middlewares, self.middlewares):
                message = await stack.enter_async_context(
                    m(message, *args, correlation_id=correlation_id, **kwargs)
                )

            return await self.method(
                message,
                *args,
                correlation_id=correlation_id,
                **kwargs,
            )


@dataclass
class BasePublisher(AsyncAPIOperation, Generic[MsgType]):
    """A base class for publishers in an asynchronous API.

    Attributes:
        title : optional title of the publisher
        _description : optional description of the publisher
        _fake_handler : boolean indicating if a fake handler is used
        calls : list of callable objects to generate AsyncAPI
        mock : MagicMock object for mocking purposes

    Methods:
        description() : returns the description of the publisher
        __call__(func) : decorator to register a function as a handler for the publisher
        publish(message, correlation_id, **kwargs) : publishes a message with optional correlation ID
    """

    schema_: Optional[Any] = field(default=None)

    calls: List[Callable[..., Any]] = field(
        init=False, default_factory=list, repr=False
    )
    middlewares: Iterable["PublisherMiddleware"] = field(
        default_factory=tuple, repr=False
    )

    _fake_handler: bool = field(default=False, repr=False)
    mock: Optional[MagicMock] = field(init=False, default=None, repr=False)

    def set_test(
        self,
        mock: MagicMock,
        with_fake: bool,
    ) -> None:
        self.mock = mock
        self._fake_handler = with_fake

    def reset_test(self) -> None:
        self._fake_handler = False
        self.mock = None

    def __call__(
        self,
        func: Callable[P_HandlerParams, T_HandlerReturn],
    ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
        """This is a Python function.

        Args:
            func: A callable object that takes `P_HandlerParams` as input and returns `T_HandlerReturn`.

        Returns:
            An instance of `HandlerCallWrapper` class.

        Raises:
            TypeError: If `func` is not callable.
        """
        handler_call: HandlerCallWrapper[
            MsgType, P_HandlerParams, T_HandlerReturn
        ] = HandlerCallWrapper(func)
        handler_call._publishers.append(self)
        self.calls.append(handler_call._original_call)
        return handler_call

    @abstractmethod
    async def publish(
        self,
        message: SendableMessage,
        *args: Any,
        correlation_id: Optional[str] = None,
        extra_middlewares: Iterable["PublisherMiddleware"] = (),
        **kwargs: Any,
    ) -> Any:
        kwargs.update(self.publish_kwargs)

        async with AsyncExitStack() as stack:
            for m in chain(extra_middlewares, self.middlewares):
                message = await stack.enter_async_context(
                    m(
                        message,
                        *args,
                        correlation_id=correlation_id,
                        **kwargs,
                    )
                )

            return await self._publish(
                message,
                *args,
                correlation_id=correlation_id,
                **kwargs,
            )

    @abstractmethod
    async def _publish(
        self,
        message: SendableMessage,
        *args: Any,
        correlation_id: Optional[str] = None,
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

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError()

    def get_payloads(self) -> List[Tuple[AnyDict, str]]:
        payloads: List[Tuple[AnyDict, str]] = []

        if self.schema_:
            params = {"response__": (self.schema_, ...)}

            call_model: CallModel[Any, Any] = CallModel(
                call=lambda: None,
                model=create_model("Fake"),
                response_model=create_model(
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

    @abstractproperty
    def publish_kwargs(self) -> AnyDict:
        raise NotImplementedError()
