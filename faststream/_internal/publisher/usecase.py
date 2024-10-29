from collections.abc import Awaitable, Iterable
from functools import partial
from inspect import Parameter, unwrap
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Optional,
)
from unittest.mock import MagicMock

from fast_depends.core import build_call_model
from fast_depends.pydantic._compat import create_model, get_config_base
from typing_extensions import Doc, override

from faststream._internal.publisher.proto import PublisherProto
from faststream._internal.subscriber.call_wrapper.call import HandlerCallWrapper
from faststream._internal.subscriber.utils import process_msg
from faststream._internal.types import (
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.message.source_type import SourceType
from faststream.specification.asyncapi.message import (
    get_model_schema,
)
from faststream.specification.asyncapi.utils import to_camelcase

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict
    from faststream._internal.publisher.proto import ProducerProto
    from faststream._internal.setup import SetupState
    from faststream._internal.types import (
        BrokerMiddleware,
        PublisherMiddleware,
    )
    from faststream.response.response import PublishCommand


class PublisherUsecase(PublisherProto[MsgType]):
    """A base class for publishers in an asynchronous API."""

    mock: Optional[MagicMock]
    calls: list[Callable[..., Any]]

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
                "Should be any python-native object annotation or `pydantic.BaseModel`.",
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
    def _setup(  # type: ignore[override]
        self, *, producer: Optional["ProducerProto"], state: Optional["SetupState"]
    ) -> None:
        self._producer = producer
        self._state = state

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

    async def _basic_publish(
        self,
        cmd: "PublishCommand",
        *,
        _extra_middlewares: Iterable["PublisherMiddleware"],
    ) -> Any:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        pub: Callable[..., Awaitable[Any]] = self._producer.publish

        for pub_m in chain(
            (
                _extra_middlewares
                or (
                    m(None, context=self._state.depends_params.context).publish_scope
                    for m in self._broker_middlewares
                )
            ),
            self._middlewares,
        ):
            pub = partial(pub_m, pub)

        await pub(cmd)

    async def _basic_request(
        self,
        cmd: "PublishCommand",
    ) -> Optional[Any]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        context = self._state.depends_params.context

        request = self._producer.request

        for pub_m in chain(
            (m(None, context=context).publish_scope for m in self._broker_middlewares),
            self._middlewares,
        ):
            request = partial(pub_m, request)

        published_msg = await request(cmd)

        response_msg: Any = await process_msg(
            msg=published_msg,
            middlewares=(
                m(published_msg, context=context) for m in self._broker_middlewares
            ),
            parser=self._producer._parser,
            decoder=self._producer._decoder,
            source_type=SourceType.Response,
        )
        return response_msg

    async def _basic_publish_batch(
        self,
        cmd: "PublishCommand",
        *,
        _extra_middlewares: Iterable["PublisherMiddleware"],
    ) -> Optional[Any]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        pub = self._producer.publish_batch

        for pub_m in chain(
            (
                _extra_middlewares
                or (
                    m(None, context=self._state.depends_params.context).publish_scope
                    for m in self._broker_middlewares
                )
            ),
            self._middlewares,
        ):
            pub = partial(pub_m, pub)

        await pub(cmd)

    def get_payloads(self) -> list[tuple["AnyDict", str]]:
        payloads: list[tuple[AnyDict, str]] = []

        if self.schema_:
            body = get_model_schema(
                call=create_model(
                    "",
                    __config__=get_config_base(),
                    response__=(self.schema_, ...),
                ),
                prefix=f"{self.name}:Message",
            )

            if body:  # pragma: no branch
                payloads.append((body, ""))

        else:
            for call in self.calls:
                call_model = build_call_model(
                    call,
                    dependency_provider=self._state.depends_params.provider,
                    serializer_cls=self._state.depends_params.serializer,
                )

                response_type = next(
                    iter(call_model.serializer.response_option.values())
                ).field_type
                if response_type is not None and response_type is not Parameter.empty:
                    body = get_model_schema(
                        create_model(
                            "",
                            __config__=get_config_base(),
                            response__=(response_type, ...),
                        ),
                        prefix=f"{self.name}:Message",
                    )
                    if body:
                        payloads.append((body, to_camelcase(unwrap(call).__name__)))

        return payloads
