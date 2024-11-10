from inspect import Parameter, unwrap
from typing import TYPE_CHECKING, Any, Optional

from fast_depends.core import build_call_model
from fast_depends.pydantic._compat import create_model, get_config_base

from faststream._internal.publisher.proto import PublisherProto
from faststream._internal.subscriber.call_wrapper.call import HandlerCallWrapper
from faststream._internal.types import (
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.specification.asyncapi.message import get_model_schema
from faststream.specification.asyncapi.utils import to_camelcase
from faststream.specification.base.proto import SpecificationEndpoint

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict


class BaseSpicificationPublisher(SpecificationEndpoint, PublisherProto[MsgType]):
    """A base class for publishers in an asynchronous API."""

    def __init__(
        self,
        *,
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        self.calls = []

        self.title_ = title_
        self.description_ = description_
        self.include_in_schema = include_in_schema
        self.schema_ = schema_

    def __call__(
        self,
        func: HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
    ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
        self.calls.append(func._original_call)
        return func

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
            di_state = self._state.get().di_state

            for call in self.calls:
                call_model = build_call_model(
                    call,
                    dependency_provider=di_state.provider,
                    serializer_cls=di_state.serializer,
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
