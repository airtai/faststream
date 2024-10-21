from typing import Annotated

from redis.asyncio.client import Redis as RedisClient

from faststream._internal.context import Context
from faststream.annotations import ContextRepo, Logger
from faststream.redis.broker.broker import RedisBroker as RB
from faststream.redis.message import UnifyRedisMessage

__all__ = (
    "ContextRepo",
    "Logger",
    "Redis",
    "RedisBroker",
    "RedisMessage",
)

RedisMessage = Annotated[UnifyRedisMessage, Context("message")]
RedisBroker = Annotated[RB, Context("broker")]
Redis = Annotated[RedisClient, Context("broker._connection")]
