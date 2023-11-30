from typing import (
    Any,
    Callable,
    Optional,
    Sequence,
    Union,
)

from fast_depends.dependencies import Depends

from faststream._compat import TypeAlias
from faststream.broker.core.asyncronous import default_filter
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
    """Delayed `RedisBroker.subscriber()` registration object"""

    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        channel: Union[Channel, PubSub, None] = None,
        *,
        list: Union[Channel, ListSub, None] = None,
        stream: Union[Channel, StreamSub, None] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[AnyRedisDict, RedisMessage]] = None,
        decoder: Optional[CustomDecoder[RedisMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[AnyRedisDict], BaseMiddleware]]
        ] = None,
        filter: Filter[RedisMessage] = default_filter,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> None: ...
