from typing import Dict

from faststream.asyncapi.base import AsyncAPIOperation
from faststream.asyncapi.schema import Channel
from faststream.asyncapi.utils import to_camelcase
from faststream.nats.handler import LogicNatsHandler
from faststream.nats.publisher import LogicPublisher


class Handler(LogicNatsHandler, AsyncAPIOperation):
    def schema(self) -> Dict[str, Channel]:
        return {}

    @property
    def name(self) -> str:
        original = super().name

        name: str
        subject = to_camelcase(self.subject)

        if original is True:
            if not self.call_name.lower().endswith(subject.lower()):
                name = f"{self.call_name}{subject}"
            else:
                name = self.call_name

        elif original is False:  # pragma: no cover
            name = f"Handler{subject}"

        else:
            name = original

        return name


class Publisher(LogicPublisher, AsyncAPIOperation):
    def schema(self) -> Dict[str, Channel]:
        return {}

    @property
    def name(self) -> str:
        return self.title or f"{self.subject.title()}Publisher"
