from redis.asyncio.client import Redis as RedisClient
from typing_extensions import Annotated

from faststream.annotations import ContextRepo, Logger, NoCast
from faststream.redis.broker.broker import RedisBroker as RB
from faststream.redis.message import UnifyRedisMessage
from faststream.utils.context import Context

__all__ = (
    "Logger",
    "ContextRepo",
    "NoCast",
    "RedisMessage",
    "RedisBroker",
    "Redis",
)

RedisMessage = Annotated[UnifyRedisMessage, Context("message")]
RedisBroker = Annotated[RB, Context("broker")]
Redis = Annotated[RedisClient, Context("broker._connection")]
