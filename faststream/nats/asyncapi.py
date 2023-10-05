from typing import Dict

from fast_depends.core import build_call_model

from faststream.asyncapi.base import AsyncAPIOperation
from faststream.asyncapi.message import get_response_schema, parse_handler_params
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


class Handler(LogicNatsHandler, AsyncAPIOperation):
    @property
    def name(self) -> str:
        original = super().name
        parsed_name = f"{self.subject}:{self.call_name}"

        return original if isinstance(original, str) else parsed_name

    def schema(self) -> Dict[str, Channel]:
        payloads = []
        for _, _, _, _, _, dep in self.calls:
            body = parse_handler_params(dep, prefix=self.name + ":Message:")
            payloads.append(body)

        return {
            self.name: Channel(
                description=self.description,
                subscribe=Operation(
                    message=Message(
                        title=f"{self.name}:Message",
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


class Publisher(LogicPublisher, AsyncAPIOperation):
    def schema(self) -> Dict[str, Channel]:
        payloads = []
        for call in self.calls:
            call_model = build_call_model(call)
            body = get_response_schema(
                call_model,
                prefix=self.name + ":Message:",
            )
            if body:
                payloads.append(body)

        return {
            self.name: Channel(
                description=self.description,
                publish=Operation(
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads),
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
        return self.title or f"{self.subject}"
