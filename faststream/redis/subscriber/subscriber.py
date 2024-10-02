from faststream.redis.schemas import ListSub, StreamSub
from faststream.redis.schemas.proto import RedisAsyncAPIProtocol
from faststream.redis.subscriber.usecase import (
    BatchListSubscriber,
    BatchStreamSubscriber,
    ChannelSubscriber,
    ListSubscriber,
    LogicSubscriber,
    StreamSubscriber,
)
from faststream.specification.asyncapi.utils import resolve_payloads
from faststream.specification.schema.bindings import ChannelBinding, redis
from faststream.specification.schema.channel import Channel
from faststream.specification.schema.message import CorrelationId, Message
from faststream.specification.schema.operation import Operation


class SpecificationSubscriber(LogicSubscriber, RedisAsyncAPIProtocol):
    """A class to represent a Redis handler."""

    def get_schema(self) -> dict[str, Channel]:
        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,
                subscribe=Operation(
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id",
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    redis=self.channel_binding,
                ),
            ),
        }


class AsyncAPIChannelSubscriber(ChannelSubscriber, SpecificationSubscriber):
    def get_name(self) -> str:
        return f"{self.channel.name}:{self.call_name}"

    @property
    def channel_binding(self) -> "redis.ChannelBinding":
        return redis.ChannelBinding(
            channel=self.channel.name,
            method="psubscribe" if self.channel.pattern else "subscribe",
        )


class _StreamSubscriberMixin(SpecificationSubscriber):
    stream_sub: StreamSub

    def get_name(self) -> str:
        return f"{self.stream_sub.name}:{self.call_name}"

    @property
    def channel_binding(self) -> "redis.ChannelBinding":
        return redis.ChannelBinding(
            channel=self.stream_sub.name,
            group_name=self.stream_sub.group,
            consumer_name=self.stream_sub.consumer,
            method="xreadgroup" if self.stream_sub.group else "xread",
        )


class AsyncAPIStreamSubscriber(StreamSubscriber, _StreamSubscriberMixin):
    pass


class AsyncAPIStreamBatchSubscriber(BatchStreamSubscriber, _StreamSubscriberMixin):
    pass


class _ListSubscriberMixin(SpecificationSubscriber):
    list_sub: ListSub

    def get_name(self) -> str:
        return f"{self.list_sub.name}:{self.call_name}"

    @property
    def channel_binding(self) -> "redis.ChannelBinding":
        return redis.ChannelBinding(
            channel=self.list_sub.name,
            method="lpop",
        )


class AsyncAPIListSubscriber(ListSubscriber, _ListSubscriberMixin):
    pass


class AsyncAPIListBatchSubscriber(BatchListSubscriber, _ListSubscriberMixin):
    pass
