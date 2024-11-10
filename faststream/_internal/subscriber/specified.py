from typing import (
    TYPE_CHECKING,
    Optional,
)

from faststream._internal.subscriber.proto import SubscriberProto
from faststream._internal.types import MsgType
from faststream.exceptions import SetupError
from faststream.specification.asyncapi.message import parse_handler_params
from faststream.specification.asyncapi.utils import to_camelcase
from faststream.specification.base.proto import SpecificationEndpoint

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict


class BaseSpicificationSubscriber(SpecificationEndpoint, SubscriberProto[MsgType]):
    def __init__(
        self,
        *,
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        self.title_ = title_
        self.description_ = description_
        self.include_in_schema = include_in_schema

    @property
    def call_name(self) -> str:
        """Returns the name of the handler call."""
        if not self.calls:
            return "Subscriber"

        return to_camelcase(self.calls[0].call_name)

    def get_description(self) -> Optional[str]:
        """Returns the description of the handler."""
        if not self.calls:  # pragma: no cover
            return None

        return self.calls[0].description

    def get_payloads(self) -> list[tuple["AnyDict", str]]:
        """Get the payloads of the handler."""
        payloads: list[tuple[AnyDict, str]] = []

        for h in self.calls:
            if h.dependant is None:
                msg = "You should setup `Handler` at first."
                raise SetupError(msg)

            body = parse_handler_params(
                h.dependant,
                prefix=f"{self.title_ or self.call_name}:Message",
            )

            payloads.append((body, to_camelcase(h.call_name)))

        if not self.calls:
            payloads.append(
                (
                    {
                        "title": f"{self.title_ or self.call_name}:Message:Payload",
                    },
                    to_camelcase(self.call_name),
                ),
            )

        return payloads
