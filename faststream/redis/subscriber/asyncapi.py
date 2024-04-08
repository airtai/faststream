from typing import TYPE_CHECKING, Dict, Iterable, Optional, Union

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
from faststream.exceptions import SetupError
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.redis.schemas.proto import RedisAsyncAPIProtocol, validate_options
from faststream.redis.subscriber.usecase import (
    BatchListSubscriber,
    BatchStreamSubscriber,
    ChannelSubscriber,
    ListSubscriber,
    LogicSubscriber,
    StreamSubscriber,
)

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream.broker.types import BrokerMiddleware
    from faststream.redis.message import UnifyRedisDict

SubsciberType: TypeAlias = Union[
    "AsyncAPIChannelSubscriber",
    "AsyncAPIStreamBatchSubscriber",
    "AsyncAPIStreamSubscriber",
    "AsyncAPIListBatchSubscriber",
    "AsyncAPIListSubscriber",
]


class AsyncAPISubscriber(LogicSubscriber, RedisAsyncAPIProtocol):
    """A class to represent a Redis handler."""

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
                bindings=ChannelBinding(
                    redis=self.channel_binding,
                ),
            )
        }

    @override
    @staticmethod
    def create(  # type: ignore[override]
        *,
        channel: Union["PubSub", str, None],
        list: Union["ListSub", str, None],
        stream: Union["StreamSub", str, None],
        # Subscriber args
        no_ack: bool = False,
        retry: bool = False,
        broker_dependencies: Iterable["Depends"] = (),
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"] = (),
        # AsyncAPI args
        title_: Optional[str] = None,
        description_: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> SubsciberType:
        validate_options(channel=channel, list=list, stream=stream)

        if (channel_sub := PubSub.validate(channel)) is not None:
            return AsyncAPIChannelSubscriber(
                channel=channel_sub,
                # basic args
                no_ack=no_ack,
                retry=retry,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # AsyncAPI args
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )

        elif (stream_sub := StreamSub.validate(stream)) is not None:
            if stream_sub.batch:
                return AsyncAPIStreamBatchSubscriber(
                    stream=stream_sub,
                    # basic args
                    no_ack=no_ack,
                    retry=retry,
                    broker_dependencies=broker_dependencies,
                    broker_middlewares=broker_middlewares,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )
            else:
                return AsyncAPIStreamSubscriber(
                    stream=stream_sub,
                    # basic args
                    no_ack=no_ack,
                    retry=retry,
                    broker_dependencies=broker_dependencies,
                    broker_middlewares=broker_middlewares,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )

        elif (list_sub := ListSub.validate(list)) is not None:
            if list_sub.batch:
                return AsyncAPIListBatchSubscriber(
                    list=list_sub,
                    # basic args
                    no_ack=no_ack,
                    retry=retry,
                    broker_dependencies=broker_dependencies,
                    broker_middlewares=broker_middlewares,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )
            else:
                return AsyncAPIListSubscriber(
                    list=list_sub,
                    # basic args
                    no_ack=no_ack,
                    retry=retry,
                    broker_dependencies=broker_dependencies,
                    broker_middlewares=broker_middlewares,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )

        else:
            raise SetupError(INCORRECT_SETUP_MSG)


class AsyncAPIChannelSubscriber(ChannelSubscriber, AsyncAPISubscriber):
    def get_name(self) -> str:
        return f"{self.channel.name}:{self.call_name}"

    @property
    def channel_binding(self) -> "redis.ChannelBinding":
        return redis.ChannelBinding(
            channel=self.channel.name,
            method="psubscribe" if self.channel.pattern else "subscribe",
        )


class _StreamSubscriberMixin(AsyncAPISubscriber):
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


class _ListSubscriberMixin(AsyncAPISubscriber):
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
