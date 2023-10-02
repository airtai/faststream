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
from faststream.asyncapi.utils import resolve_payloads, to_camelcase
from faststream.nats.handler import LogicNatsHandler
from faststream.nats.publisher import LogicPublisher


class Handler(LogicNatsHandler, AsyncAPIOperation):
    def schema(self) -> Dict[str, Channel]:
        name = f"{self.subject}/{self.call_name}"

        payloads = []
        for _, _, _, _, _, dep in self.calls:
            body = parse_handler_params(dep, prefix=name)
            payloads.append(body)

        return {
            name: Channel(
                description=self.description,
                subscribe=Operation(
                    message=Message(
                        title=f"{name}/Message",
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

    @property
    def name(self) -> str:
        return self.call_name


class Publisher(LogicPublisher, AsyncAPIOperation):
    def schema(self) -> Dict[str, Channel]:
        payloads = []
        for call in self.calls:
            call_model = build_call_model(call)
            body = get_response_schema(
                call_model,
                prefix=to_camelcase(call_model.call_name),
            )
            if body:
                payloads.append(body)

        return {
            self.name: Channel(
                description=self.description,
                publish=Operation(
                    message=Message(
                        title=f"{self.name}/Message",
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
        return self.title or f"{self.subject}/Publisher"
