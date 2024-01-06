from typing import (
    Any,
    Callable,
    Sequence,
)

from fast_depends.dependencies import Depends
from typing_extensions import TypeAlias

from faststream.broker.core.asynchronous import default_filter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    T_HandlerReturn,
)
from faststream.redis.message import AnyRedisDict, RedisMessage
from faststream.redis.schemas import ListSub, PubSub, StreamSub

Channel: TypeAlias = str

class RedisRoute:
    """Delayed `RedisBroker.subscriber()` registration object."""

    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        channel: Channel | PubSub | None = None,
        *,
        list: Channel | ListSub | None = None,
        stream: Channel | StreamSub | None = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: CustomParser[AnyRedisDict, RedisMessage] | None = None,
        decoder: CustomDecoder[RedisMessage] | None = None,
        middlewares: Sequence[Callable[[AnyRedisDict], BaseMiddleware]] | None = None,
        filter: Filter[RedisMessage] = default_filter,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> None: ...
