from typing import Any, Optional
from uuid import uuid4

from redis.asyncio.client import PubSub, Redis

from faststream.broker.parsers import resolve_custom_func
from faststream.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    AsyncDecoder,
    AsyncParser,
)
from faststream.exceptions import WRONG_PUBLISH_ARGS
from faststream.redis.message import PubSubMessage, RedisMessage
from faststream.redis.parser import RawMessage, RedisParser
from faststream.types import AnyDict, DecodedMessage, SendableMessage
from faststream.utils.functions import timeout_scope


class RedisFastProducer:
    _connection: Redis
    _decoder: AsyncDecoder[Any]
    _parser: AsyncParser[PubSubMessage, Any]

    def __init__(
        self,
        connection: Redis,
        parser: Optional[AsyncCustomParser[PubSubMessage, RedisMessage]],
        decoder: Optional[AsyncCustomDecoder[RedisMessage]],
    ):
        self._connection = connection
        self._parser = resolve_custom_func(parser, RedisParser.parse_message)
        self._decoder = resolve_custom_func(decoder, RedisParser.decode_message)

    async def publish(
        self,
        message: SendableMessage,
        channel: str,
        reply_to: str = "",
        headers: Optional[AnyDict] = None,
        correlation_id: Optional[str] = None,
        *,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[DecodedMessage]:
        psub: Optional[PubSub] = None
        if rpc is True:
            if reply_to:
                raise WRONG_PUBLISH_ARGS

            reply_to = str(uuid4())
            psub = self._connection.pubsub()
            await psub.subscribe(reply_to)

        await self._connection.publish(
            channel,
            RawMessage.encode(
                message=message,
                reply_to=reply_to,
                headers=headers,
                correlation_id=correlation_id,
            ),
        )

        if psub is None:
            return None

        else:
            m = None
            with timeout_scope(rpc_timeout, raise_timeout):
                # skip subscribe message
                await psub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=rpc_timeout or 0.0,
                )

                # get real response
                m = await psub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=rpc_timeout or 0.0,
                )

            await psub.unsubscribe()
            await psub.reset()

            if m is None:
                if raise_timeout:
                    raise TimeoutError()
                else:
                    return None
            else:
                return await self._decoder(await self._parser(m))
