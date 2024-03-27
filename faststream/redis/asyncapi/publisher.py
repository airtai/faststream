from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union

from typing_extensions import TypeAlias, override

from faststream.asyncapi.schema import (
    Channel,
    ChannelBinding,
    CorrelationId,
    Message,
    Operation,
)
from faststream.asyncapi.schema.bindings import redis
from faststream.asyncapi.utils import resolve_payloads
from faststream.broker.core.publisher import ExtendedPublisherProtocol
from faststream.exceptions import SetupError
from faststream.redis.asyncapi.base import RedisAsyncAPIProtocol, validate_options
from faststream.redis.publisher import (
    ChannelPublisher,
    ListBatchPublisher,
    ListPublisher,
    StreamPublisher,
)
from faststream.redis.schemas import INCORRECT_SETUP_MSG

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware
    from faststream.redis.schemas import ListSub, PubSub, StreamSub
    from faststream.types import AnyDict


PublisherType: TypeAlias = Union[
    "ChannelAsyncAPIPublisher",
    "StreamAsyncAPIPublisher",
    "ListAsyncAPIPublisher",
    "BatchListAsyncAPIPublisher",
]

class Publisher(RedisAsyncAPIProtocol, ExtendedPublisherProtocol):
    """A class to represent a Redis publisher."""

    _producer: Any

    def get_schema(self) -> Dict[str, Channel]:
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
                    redis=self.channel_binding,
                ),
            )
        }

    @override
    @staticmethod
    def create(  # type: ignore[override]
        *,
        channel: Optional["PubSub"],
        list: Optional["ListSub"],
        stream: Optional["StreamSub"],
        headers: Optional["AnyDict"] = None,
        reply_to: str = "",
        middlewares: Iterable["PublisherMiddleware"] = (),
        # AsyncAPI args
        title_: Optional[str] = None,
        description_: Optional[str] = None,
        schema_: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> PublisherType:
        validate_options(channel=channel, list=list, stream=stream)

        if channel is not None:
            return ChannelAsyncAPIPublisher(
                channel=channel,
                # basic args
                headers=headers,
                reply_to=reply_to,
                middlewares=middlewares,
                # AsyncAPI args
                title_=title_,
                description_=description_,
                schema_=schema_,
                include_in_schema=include_in_schema,
            )

        elif stream is not None:
            return StreamAsyncAPIPublisher(
                stream=stream,
                # basic args
                headers=headers,
                reply_to=reply_to,
                middlewares=middlewares,
                # AsyncAPI args
                title_=title_,
                description_=description_,
                schema_=schema_,
                include_in_schema=include_in_schema,
            )

        elif list is not None:
            if list.batch:
                return BatchListAsyncAPIPublisher(
                    list=list,
                    # basic args
                    headers=headers,
                    reply_to=reply_to,
                    middlewares=middlewares,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    schema_=schema_,
                    include_in_schema=include_in_schema,
                )
            else:
                return ListAsyncAPIPublisher(
                    list=list,
                    # basic args
                    headers=headers,
                    reply_to=reply_to,
                    middlewares=middlewares,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    schema_=schema_,
                    include_in_schema=include_in_schema,
                )

        else:
            raise SetupError(INCORRECT_SETUP_MSG)


class ChannelAsyncAPIPublisher(ChannelPublisher, Publisher):
    def get_name(self) -> str:
        return f"{self.channel.name}:Publisher"

    @property
    def channel_binding(self) -> redis.ChannelBinding:
        return redis.ChannelBinding(
            channel=self.channel.name,
            method="publish",
        )


class _ListPublisherMixin(Publisher):
    list: "ListSub"

    def get_name(self) -> str:
        return f"{self.list.name}:Publisher"

    @property
    def channel_binding(self) -> redis.ChannelBinding:
        return redis.ChannelBinding(
            channel=self.list.name,
            method="rpush",
        )


class ListAsyncAPIPublisher(ListPublisher, _ListPublisherMixin):
    pass


class BatchListAsyncAPIPublisher(ListBatchPublisher, _ListPublisherMixin):
    pass


class StreamAsyncAPIPublisher(StreamPublisher, Publisher):
    def get_name(self) -> str:
        return f"{self.stream.name}:Publisher"

    @property
    def channel_binding(self) -> redis.ChannelBinding:
        return redis.ChannelBinding(
            channel=self.stream.name,
            method="xadd",
        )
