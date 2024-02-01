from abc import abstractproperty
from typing import Dict, Optional, Hashable

from faststream.asyncapi.schema import (
    Channel,
    ChannelBinding,
    CorrelationId,
    Message,
    Operation,
)
from faststream.redis.schemas import ListSub, PubSub, StreamSub
from faststream.asyncapi.schema.bindings import redis
from faststream.asyncapi.utils import resolve_payloads
from faststream.redis.handler import ListHandler, StreamHandler, ChannelHandler, BaseRedisHandler
from faststream.redis.publisher import LogicPublisher


class Handler:
    """A class to represent a Redis handler."""
    @staticmethod
    def get_routing_hash(channel: Hashable) -> int:
        return hash(channel)

    @abstractproperty
    def binding(self) -> redis.ChannelBinding:
        raise NotImplementedError()

    def get_name(self) -> str:
        return f"{self.channel_name}:{self.call_name}"

    def get_schema(self) -> Dict[str, Channel]:
        payloads = self.get_payloads()

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
                bindings=ChannelBinding(redis=self.binding,),
            )
        }

    @staticmethod
    def create(
        *,
        channel: Optional[PubSub],
        list: Optional[ListSub],
        stream: Optional[StreamSub],
        **kwargs,
    ) -> BaseRedisHandler:
        if stream is not None:
            return StreamAsyncAPIHandler(stream=stream, **kwargs)
        
        elif channel is not None:
            return ChannelAsyncAPIHandler(channel=channel, **kwargs)

        else:
            return ListAsyncAPIHandler(list=list, **kwargs)


class ChannelAsyncAPIHandler(Handler, ChannelHandler):
    @property
    def binding(self) -> redis.ChannelBinding:
        return redis.ChannelBinding(
            channel=self.channel_name,
            method="psubscribe" if self.channel.pattern else "subscribe"
        )


class StreamAsyncAPIHandler(Handler, StreamHandler):
    @property
    def binding(self) -> redis.ChannelBinding:
        return redis.ChannelBinding(
            channel=self.channel_name,
            group_name=self.stream_sub.group,
            consumer_name=self.stream_sub.consumer,
            method="xreadgroup" if self.stream_sub.group else "xread",
        )


class ListAsyncAPIHandler(Handler, ListHandler):
    @property
    def binding(self) -> redis.ChannelBinding:
        return redis.ChannelBinding(
            channel=self.channel_name,
            method="lpop",
        )


class Publisher(LogicPublisher):
    """A class to represent a Redis publisher."""

    def get_name(self) -> str:
        return f"{self.channel_name}:Publisher"

    def get_schema(self) -> Dict[str, Channel]:
        payloads = self.get_payloads()

        method = None
        if self.list is not None:
            method = "rpush"
        elif self.channel is not None:
            method = "publish"
        elif self.stream is not None:
            method = "xadd"
        else:
            raise AssertionError("unreachable")

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
