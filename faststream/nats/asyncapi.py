from typing import Dict

from faststream.asyncapi.schema import (
    Channel,
    ChannelBinding,
    CorrelationId,
    Message,
    Operation,
)
from faststream.asyncapi.schema.bindings import nats
from faststream.asyncapi.utils import resolve_payloads
from faststream.nats.handler import LogicNatsHandler
from faststream.nats.publisher import LogicPublisher


class Handler(LogicNatsHandler):
    def schema(self) -> Dict[str, Channel]:
        if not self.include_in_schema:
            return {}

        payloads = self.get_payloads()
        handler_name = self._title or f"{self.subject}:{self.call_name}"
        return {
            handler_name: Channel(
                description=self.description,
                subscribe=Operation(
                    message=Message(
                        title=f"{handler_name}:Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    nats=nats.ChannelBinding(
                        subject=self.subject,
                        queue=self.queue or None,
                    )
                ),
            )
        }


class Publisher(LogicPublisher):
    def schema(self) -> Dict[str, Channel]:
        if not self.include_in_schema:
            return {}

        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,
                publish=Operation(
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads, "Publisher"),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    nats=nats.ChannelBinding(
                        subject=self.subject,
                    )
                ),
            )
        }

    @property
    def name(self) -> str:
        return self.title or f"{self.subject}:Publisher"
