from typing import TYPE_CHECKING, Any, Optional
from uuid import uuid4

from faststream.broker.parsers import encode_message, resolve_custom_func
from faststream.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    AsyncDecoder,
    AsyncParser,
)
from faststream.exceptions import WRONG_PUBLISH_ARGS, SetupError
from faststream.redis.message import DATA_KEY
from faststream.redis.parser import RawMessage, RedisPubSubParser
from faststream.redis.schemas import INCORRECT_SETUP_MSG
from faststream.types import AnyDict, SendableMessage
from faststream.utils.functions import timeout_scope

if TYPE_CHECKING:
    from redis.asyncio.client import PubSub, Redis

    from faststream.broker.message import StreamMessage


class RedisFastProducer:
    """A class to represent a Redis producer."""

    _connection: "Redis[bytes]"
    _decoder: AsyncDecoder[Any]
    _parser: AsyncParser["AnyDict"]

    def __init__(
        self,
        connection: "Redis[bytes]",
        parser: Optional["AsyncCustomParser[AnyDict]"],
        decoder: Optional["AsyncCustomDecoder[StreamMessage[AnyDict]]"],
    ) -> None:
        """Initialize the Redis producer.

        Args:
            connection: The Redis connection.
            parser: The parser.
            decoder: The decoder.
        """
        self._connection = connection
        self._parser = resolve_custom_func(
            parser,  # type: ignore[arg-type,assignment]
            RedisPubSubParser.parse_message,
        )
        self._decoder = resolve_custom_func(decoder, RedisPubSubParser.decode_message)

    async def publish(
        self,
        message: SendableMessage,
        *,
        channel: Optional[str] = None,
        list: Optional[str] = None,
        stream: Optional[str] = None,
        maxlen: Optional[int] = None,
        headers: Optional[AnyDict] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[Any]:
        if not any((channel, list, stream)):
            raise SetupError(INCORRECT_SETUP_MSG)

        psub: Optional["PubSub"] = None
        if rpc:
            if reply_to:
                raise WRONG_PUBLISH_ARGS

            reply_to = str(uuid4())
            psub = self._connection.pubsub()
            await psub.subscribe(reply_to)

        msg = RawMessage.encode(
            message=message,
            reply_to=reply_to,
            headers=headers,
            correlation_id=correlation_id,
        )

        if channel is not None:
            await self._connection.publish(channel, msg)
        elif list is not None:
            await self._connection.rpush(list, msg)
        elif stream is not None:
            await self._connection.xadd(
                name=stream,
                fields={DATA_KEY: msg},
                maxlen=maxlen,
            )
        else:
            raise AssertionError("unreachable")

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
            await psub.aclose()  # type: ignore[attr-defined]

            if m is None:
                if raise_timeout:
                    raise TimeoutError()
                else:
                    return None
            else:
                return await self._decoder(await self._parser(m))

    async def publish_batch(
        self,
        *msgs: SendableMessage,
        list: str,
    ) -> None:
        batch = (encode_message(msg)[0] for msg in msgs)
        await self._connection.rpush(list, *batch)
