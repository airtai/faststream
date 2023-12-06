from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Sequence,
    Union,
)

from fast_depends.dependencies import Depends

from faststream._compat import override
from faststream.broker.core.asyncronous import default_filter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.router import BrokerRouter
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.redis.asyncapi import Publisher
from faststream.redis.message import AnyRedisDict, RedisMessage
from faststream.redis.schemas import ListSub, PubSub, StreamSub
from faststream.redis.shared.router import RedisRoute
from faststream.types import AnyDict

class RedisRouter(BrokerRouter[int, AnyRedisDict]):
    _publishers: Dict[int, Publisher]  # type: ignore[assignment]

    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[RedisRoute] = (),
        *,
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[AnyRedisDict, RedisMessage]] = None,
        decoder: Optional[CustomDecoder[RedisMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[AnyRedisDict], BaseMiddleware]]
        ] = None,
        include_in_schema: bool = True,
    ): ...
    @override
    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> int:  # type: ignore[override]
        ...
    @override
    @staticmethod
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        channel: Union[str, PubSub, None] = None,
        *,
        list: Union[str, ListSub, None] = None,
        stream: Union[str, StreamSub, None] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[AnyRedisDict, RedisMessage]] = None,
        decoder: Optional[CustomDecoder[RedisMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[AnyRedisDict], BaseMiddleware]]
        ] = None,
        filter: Filter[RedisMessage] = default_filter,
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Any, P_HandlerParams, T_HandlerReturn],
    ]: ...
    @override
    def publisher(  # type: ignore[override]
        self,
        channel: Union[str, PubSub, None] = None,
        list: Union[str, ListSub, None] = None,
        stream: Union[str, StreamSub, None] = None,
        headers: Optional[AnyDict] = None,
        reply_to: str = "",
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> Publisher: ...
