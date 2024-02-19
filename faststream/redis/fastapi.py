from typing import Any, Callable, Optional, Sequence, Union

from fastapi import Depends
from redis.asyncio.client import Redis as RedisClient
from typing_extensions import Annotated, override

from faststream.broker.fastapi.context import Context, ContextRepo, Logger
from faststream.broker.fastapi.router import StreamRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.redis.broker import RedisBroker as RB
from faststream.redis.message import AnyRedisDict
from faststream.redis.message import RedisMessage as RM
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub

__all__ = (
    "Context",
    "Logger",
    "ContextRepo",
    "RedisRouter",
    "RedisMessage",
    "RedisBroker",
    "Redis",
)

RedisMessage = Annotated[RM, Context("message")]
RedisBroker = Annotated[RB, Context("broker")]
Redis = Annotated[RedisClient, Context("broker._connection")]


class RedisRouter(StreamRouter[AnyRedisDict]):
    """A class to represent a Redis router."""

    broker_class = RB

    def subscriber(
        self,
        channel: Union[str, PubSub, None] = None,
        *,
        list: Union[str, ListSub, None] = None,
        stream: Union[str, StreamSub, None] = None,
        dependencies: Optional[Sequence[Depends]] = None,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[AnyRedisDict, P_HandlerParams, T_HandlerReturn],
    ]:
        channel = PubSub.validate(channel)
        list = ListSub.validate(list)
        stream = StreamSub.validate(stream)

        if (any_of := channel or list or stream) is None:
            raise ValueError(INCORRECT_SETUP_MSG)

        return super().subscriber(
            path=any_of.name,
            channel=channel,
            stream=stream,
            list=list,
            dependencies=dependencies,
            **broker_kwargs,
        )

    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: RB,
        including_broker: RB,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(h.channel_name)
