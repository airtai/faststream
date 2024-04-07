from redis.asyncio.client import Redis as RedisClient
from typing_extensions import Annotated

from faststream.broker.fastapi.context import Context, ContextRepo, Logger
from faststream.redis.broker.broker import RedisBroker as RB
from faststream.redis.fastapi.fastapi import RedisRouter
from faststream.redis.message import BaseMessage as RM  # noqa: N814

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
