from abc import ABC
from inspect import unwrap
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    List,
    Optional,
    Tuple,
)
from unittest.mock import MagicMock

from fast_depends._compat import create_model, get_config_base
from fast_depends.core import CallModel, build_call_model
from typing_extensions import Annotated, Doc, override

from faststream.asyncapi.abc import AsyncAPIOperation
from faststream.asyncapi.message import get_response_schema
from faststream.asyncapi.utils import to_camelcase
from faststream.broker.publisher.proto import PublisherProto
from faststream.broker.types import (
    BrokerMiddleware,
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper.call import HandlerCallWrapper

if TYPE_CHECKING:
    from faststream.broker.publisher.proto import ProducerProto
    from faststream.broker.types import (
        BrokerMiddleware,
        PublisherMiddleware,
    )
    from faststream.types import AnyDict


class PublisherUsecase(
    ABC,
    AsyncAPIOperation,
    PublisherProto[MsgType],
):
    """A base class for publishers in an asynchronous API."""

    mock: Optional[MagicMock]
    calls: List[Callable[..., Any]]

    def __init__(
        self,
        *,
        broker_middlewares: Annotated[
            Iterable["BrokerMiddleware[MsgType]"],
            Doc("Top-level middlewares to use in direct `.publish` call."),
        ],
        middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Publisher middlewares."),
        ],
        # AsyncAPI args
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
        self.calls = []
        self._middlewares = middlewares
        self._broker_middlewares = broker_middlewares
        self._producer = None

        self._fake_handler = False
        self.mock = None

        # AsyncAPI
        self.title_ = title_
        self.description_ = description_
        self.include_in_schema = include_in_schema
        self.schema_ = schema_

    def add_middleware(self, middleware: "BrokerMiddleware[MsgType]") -> None:
        self._broker_middlewares = (*self._broker_middlewares, middleware)

    @override
    def setup(  # type: ignore[override]
        self,
        *,
        producer: Optional["ProducerProto"],
    ) -> None:
        self._producer = producer

    def set_test(
        self,
        *,
        mock: Annotated[
            MagicMock,
            Doc("Mock object to check in tests."),
        ],
        with_fake: Annotated[
            bool,
            Doc("Whetevet publisher's fake subscriber created or not."),
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

    def get_payloads(self) -> List[Tuple["AnyDict", str]]:
        payloads: List[Tuple["AnyDict", str]] = []

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
