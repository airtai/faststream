from typing import TYPE_CHECKING

from faststream.redis.publisher.usecase import (
    ChannelPublisher,
    ListBatchPublisher,
    ListPublisher,
    LogicPublisher,
    StreamPublisher,
)
from faststream.redis.schemas.proto import RedisSpecificationProtocol
from faststream.specification.asyncapi.utils import resolve_payloads
from faststream.specification.schema.bindings import ChannelBinding, redis
from faststream.specification.schema.channel import Channel
from faststream.specification.schema.message import CorrelationId, Message
from faststream.specification.schema.operation import Operation

if TYPE_CHECKING:
    from faststream.redis.schemas import ListSub


class SpecificationPublisher(LogicPublisher, RedisSpecificationProtocol):
    """A class to represent a Redis publisher."""

    def get_schema(self) -> dict[str, Channel]:
        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,
                publish=Operation(
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads, "Publisher"),
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


class SpecificationChannelPublisher(ChannelPublisher, SpecificationPublisher):
    def get_name(self) -> str:
        return f"{self.channel.name}:Publisher"

    @property
    def channel_binding(self) -> "redis.ChannelBinding":
        return redis.ChannelBinding(
            channel=self.channel.name,
            method="publish",
        )


class _ListPublisherMixin(SpecificationPublisher):
    list: "ListSub"

    def get_name(self) -> str:
        return f"{self.list.name}:Publisher"

    @property
    def channel_binding(self) -> "redis.ChannelBinding":
        return redis.ChannelBinding(
            channel=self.list.name,
            method="rpush",
        )


class SpecificationListPublisher(ListPublisher, _ListPublisherMixin):
    pass


class SpecificationListBatchPublisher(ListBatchPublisher, _ListPublisherMixin):
    pass


class SpecificationStreamPublisher(StreamPublisher, SpecificationPublisher):
    def get_name(self) -> str:
        return f"{self.stream.name}:Publisher"

    @property
    def channel_binding(self) -> "redis.ChannelBinding":
        return redis.ChannelBinding(
            channel=self.stream.name,
            method="xadd",
        )
