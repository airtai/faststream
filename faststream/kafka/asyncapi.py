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
from faststream.asyncapi.schema.bindings import kafka
from faststream.asyncapi.utils import resolve_payloads, to_camelcase
from faststream.kafka.handler import LogicHandler
from faststream.kafka.publisher import LogicPublisher


class Handler(LogicHandler, AsyncAPIOperation):
    def schema(self) -> Dict[str, Channel]:
        name: str
        if self.name is True:
            name, add_topic = self.call_name, True
        elif self.name is False:  # pragma: no cover
            name, add_topic = "Handler", True
        else:
            name, add_topic = self.name, False

        channels = {}

        for t in self.topics:
            if add_topic:
                t_ = to_camelcase(t)
                if not name.lower().endswith(t_.lower()):
                    name_ = f"{name}{t_}"
                else:
                    name_ = name
            else:
                name_ = name

            payloads = []
            for _, _, _, _, _, dep in self.calls:
                body = parse_handler_params(dep, prefix=name_)
                payloads.append(body)

            channels[name_] = Channel(
                description=self.description,
                subscribe=Operation(
                    message=Message(
                        title=f"{name_}Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(kafka=kafka.ChannelBinding(topic=t)),
            )

        return channels


class Publisher(LogicPublisher, AsyncAPIOperation):
    @property
    def name(self) -> str:
        return self.title or f"{self.topic.title()}Publisher"

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
                        title=f"{self.name}Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(kafka=kafka.ChannelBinding(topic=self.topic)),
            )
        }
