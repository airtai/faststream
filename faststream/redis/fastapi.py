from redis.asyncio.client import Redis as RedisClient

from faststream._compat import Annotated, override
from faststream.broker.fastapi.context import Context, ContextRepo, Logger
from faststream.broker.fastapi.router import StreamRouter
from faststream.redis.broker import RedisBroker as RB
from faststream.redis.message import AnyRedisDict
from faststream.redis.message import RedisMessage as RM

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
    broker_class = RB

    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: RB,
        including_broker: RB,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(h.channel_name)
