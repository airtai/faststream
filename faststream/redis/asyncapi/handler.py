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
from faststream.broker.core.handler import HandlerProtocol
from faststream.broker.utils import get_watcher_context
from faststream.exceptions import SetupError
from faststream.redis.asyncapi.base import RedisAsyncAPIProtocol, validate_options
from faststream.redis.handler import (
    BatchListHandler,
    BatchStreamHandler,
    ChannelHandler,
    ListHandler,
    StreamHandler,
)
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.types import AnyDict

if TYPE_CHECKING:
    from faststream.broker.types import BrokerMiddleware
    from faststream.types import LoggerProtocol


HandlerType: TypeAlias = Union[
    "ChannelAsyncAPIHandler",
    "BatchStreamAsyncAPIHandler",
    "StreamAsyncAPIHandler",
    "BatchListAsyncAPIHandler",
    "ListAsyncAPIHandler",
]

class Handler(RedisAsyncAPIProtocol, HandlerProtocol[Any]):
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
        channel: Optional[PubSub],
        list: Optional[ListSub],
        stream: Optional[StreamSub],
        # base options
        extra_context: Optional["AnyDict"] = None,
        graceful_timeout: Optional[float] = None,
        middlewares: Iterable["BrokerMiddleware[Any]"] = (),
        logger: Optional["LoggerProtocol"] = None,
        retry: bool = False,
        no_ack: bool = False,
        # AsyncAPI
        title_: Optional[str] = None,
        description_: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> HandlerType:
        validate_options(channel=channel, list=list, stream=stream)

        watcher = get_watcher_context(logger, no_ack, retry)

        if channel is not None:
            return ChannelAsyncAPIHandler(
                channel=channel,
                # basic args
                watcher=watcher,
                middlewares=middlewares,
                extra_context=extra_context or {},
                graceful_timeout=graceful_timeout,
                # AsyncAPI args
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )

        elif stream is not None:
            if stream.batch:
                return BatchStreamAsyncAPIHandler(
                    stream=stream,
                    # basic args
                    watcher=watcher,
                    middlewares=middlewares,
                    extra_context=extra_context or {},
                    graceful_timeout=graceful_timeout,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )
            else:
                return StreamAsyncAPIHandler(
                    stream=stream,
                    # basic args
                    watcher=watcher,
                    middlewares=middlewares,
                    extra_context=extra_context or {},
                    graceful_timeout=graceful_timeout,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )

        elif list is not None:
            if list.batch:
                return BatchListAsyncAPIHandler(
                    list=list,
                    # basic args
                    watcher=watcher,
                    middlewares=middlewares,
                    extra_context=extra_context or {},
                    graceful_timeout=graceful_timeout,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )
            else:
                return ListAsyncAPIHandler(
                    list=list,
                    # basic args
                    watcher=watcher,
                    middlewares=middlewares,
                    extra_context=extra_context or {},
                    graceful_timeout=graceful_timeout,
                    # AsyncAPI args
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )

        else:
            raise SetupError(INCORRECT_SETUP_MSG)


class ChannelAsyncAPIHandler(ChannelHandler, Handler):
    def get_name(self) -> str:
        return f"{self.channel.name}:{self.call_name}"

    @property
    def channel_binding(self) -> redis.ChannelBinding:
        return redis.ChannelBinding(
            channel=self.channel.name,
            method="psubscribe" if self.channel.pattern else "subscribe",
        )


class _StreamHandlerMixin(Handler):
    stream_sub: StreamSub

    def get_name(self) -> str:
        return f"{self.stream_sub.name}:{self.call_name}"

    @property
    def channel_binding(self) -> redis.ChannelBinding:
        return redis.ChannelBinding(
            channel=self.stream_sub.name,
            group_name=self.stream_sub.group,
            consumer_name=self.stream_sub.consumer,
            method="xreadgroup" if self.stream_sub.group else "xread",
        )


class StreamAsyncAPIHandler(StreamHandler, _StreamHandlerMixin):
    pass


class BatchStreamAsyncAPIHandler(BatchStreamHandler, _StreamHandlerMixin):
    pass


class _ListHandlerMixin(Handler):
    list_sub: ListSub

    def get_name(self) -> str:
        return f"{self.list_sub.name}:{self.call_name}"

    @property
    def channel_binding(self) -> redis.ChannelBinding:
        return redis.ChannelBinding(
            channel=self.list_sub.name,
            method="lpop",
        )


class ListAsyncAPIHandler(ListHandler, _ListHandlerMixin):
    pass


class BatchListAsyncAPIHandler(BatchListHandler, _ListHandlerMixin):
    pass
