from redis.asyncio.client import Redis as RedisClient
from typing_extensions import Annotated

from faststream.annotations import ContextRepo, Logger, NoCast
from faststream.broker.message import StreamMessage as BrokerStreamMessage
from faststream.redis.broker import RedisBroker as RB
from faststream.redis.message import BaseMessage as BM
from faststream.utils.context import Context

__all__ = (
    "Logger",
    "ContextRepo",
    "NoCast",
    "RedisMessage",
    "RedisBroker",
    "Redis",
)

RedisMessage = Annotated[BrokerStreamMessage[BM], Context("message")]
RedisBroker = Annotated[RB, Context("broker")]
Redis = Annotated[RedisClient, Context("broker._connection")]
