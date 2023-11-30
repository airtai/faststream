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
    @property
    def name(self) -> str:
        return self._title or f"{self.channel_name}:{self.call_name}"

    def schema(self) -> Dict[str, Channel]:
        if not self.include_in_schema:
            return {}

        payloads = self.get_payloads()

        method = None
        if self.list_sub is not None:
            method = "lpop"

        elif (ch := self.channel) is not None:
            if ch.pattern:
                method = "psubscribe"
            else:
                method = "subscribe"

        elif (stream := self.stream_sub) is not None:
            if stream.group:
                method = "xreadgroup"
            else:
                method = "xread"

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
                    redis=redis.ChannelBinding(
                        channel=self.channel_name,
                        group_name=getattr(self.stream_sub, "group", None),
                        consumer_name=getattr(self.stream_sub, "consumer", None),
                        method=method,
                    )
                ),
            )
        }


class Publisher(LogicPublisher):
    def schema(self) -> Dict[str, Channel]:
        if not self.include_in_schema:
            return {}

        payloads = self.get_payloads()

        method = None
        if self.list is not None:
            method = "rpush"
        elif self.channel is not None:
            method = "publish"
        elif self.stream is not None:
            method = "xadd"

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
                        channel=self.channel_name,
                        method=method,
                    )
                ),
            )
        }

    @property
    def name(self) -> str:
        return self.title or f"{self.channel_name}:Publisher"
