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
from faststream.asyncapi.utils import resolve_payloads
from faststream.kafka.handler import LogicHandler
from faststream.kafka.publisher import LogicPublisher


class Handler(LogicHandler, AsyncAPIOperation):
    """A class to handle logic and async API operations.

    Methods:
        schema() -> Dict[str, Channel]: Returns a dictionary of channels.
    !!! note

        The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
    """

    def schema(self) -> Dict[str, Channel]:
        channels = {}

        for t in self.topics:
            payloads = []
            handler_name = (
                self.name if isinstance(self.name, str) else f"{t}/{self.call_name}"
            )
            for _, _, _, _, _, dep in self.calls:
                body = parse_handler_params(dep, prefix=handler_name + "/Message/")
                payloads.append(body)

            print(payloads)
            channels[handler_name] = Channel(
                description=self.description,
                subscribe=Operation(
                    message=Message(
                        title=f"{handler_name}/Message",
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
    """A class representing a publisher.

    Attributes:
        name : name of the publisher

    Methods:
        schema() : returns the schema for the publisher

    Raises:
        NotImplementedError: If silent animals are not supported
    !!! note

        The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
    """

    def schema(self) -> Dict[str, Channel]:
        payloads = []
        for call in self.calls:
            call_model = build_call_model(call)
            body = get_response_schema(
                call_model,
                prefix=self.topic + "/Message/",
            )
            if body:
                payloads.append(body)

        return {
            self.title
            or self.topic: Channel(
                description=self.description,
                publish=Operation(
                    message=Message(
                        title=f"{self.topic}/Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(kafka=kafka.ChannelBinding(topic=self.topic)),
            )
        }
