from typing import Dict

from faststream.asyncapi.schema import (
    Channel,
    ChannelBinding,
    CorrelationId,
    Message,
    Operation,
)
from faststream.asyncapi.schema.bindings import redis
from faststream.asyncapi.utils import resolve_payloads
from faststream.redis.handler import LogicRedisHandler
from faststream.redis.publisher import LogicPublisher


class Handler(LogicRedisHandler):
    def schema(self) -> Dict[str, Channel]:
        payloads = self.get_payloads()
        handler_name = self._title or f"{self.channel}:{self.call_name}"
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
                    redis=redis.ChannelBinding(
                        channel=self.channel,
                        method="psubscribe" if self.pattern else "subscribe",
                    )
                ),
            )
        }


class Publisher(LogicPublisher):
    def schema(self) -> Dict[str, Channel]:
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
                    redis=redis.ChannelBinding(
                        channel=self.channel,
                    )
                ),
            )
        }

    @property
    def name(self) -> str:
        return self.title or f"{self.channel}:Publisher"
