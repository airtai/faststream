import asyncio
from typing import Optional, Dict, Any
from uuid import uuid4
from secrets import token_hex

import anyio
import nats
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js import JetStreamContext

from faststream.broker.parsers import resolve_custom_func, encode_message
from faststream.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    AsyncDecoder,
    AsyncParser,
)
from faststream.exceptions import WRONG_PUBLISH_ARGS
from faststream.nats.parser import Parser
from faststream.types import DecodedMessage, SendableMessage


class NatsFastProducer:
    _connection: Client
    _decoder: AsyncDecoder[Msg]
    _parser: AsyncParser[Msg]

    def __init__(
        self,
        connection: Client,
        parser: Optional[AsyncCustomParser[Msg]],
        decoder: Optional[AsyncCustomDecoder[Msg]],
    ):
        self._connection = connection
        self._parser = resolve_custom_func(parser, Parser.parse_message)
        self._decoder = resolve_custom_func(decoder, Parser.decode_message)

    async def publish(
        self,
        message: SendableMessage,
        subject: str,
        reply_to: str = "",
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        *,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[DecodedMessage]:
        payload, content_type = encode_message(message)

        headers_to_send = {
            "content-type": content_type or "",
            "correlation_id": correlation_id or str(uuid4()),
            **(headers or {}),
        }

        client = self._connection

        if rpc:
            if reply_to:
                raise WRONG_PUBLISH_ARGS

            token = client._nuid.next()
            token.extend(token_hex(2).encode())
            reply_to = token.decode()

            future: asyncio.Future[Msg] = asyncio.Future()
            sub = await client.subscribe(reply_to, future=future, max_msgs=1)
            await sub.unsubscribe(limit=1)

        await client.publish(
            subject=subject,
            payload=payload,
            reply=reply_to,
            headers=headers_to_send,
        )

        if rpc:
            if raise_timeout:
                scope = anyio.fail_after
            else:
                scope = anyio.move_on_after

            msg: Any = None
            with scope(rpc_timeout):
                msg = await future

            if msg:
                if msg.headers:  # pragma: no branch
                    if (
                        msg.headers.get(nats.js.api.Header.STATUS)
                        == nats.aio.client.NO_RESPONDERS_STATUS
                    ):
                        raise nats.errors.NoRespondersError
                return await self._decoder(await self._parser(msg))


class NatsJSFastProducer:
    _connection: JetStreamContext
    _decoder: AsyncDecoder[Msg]
    _parser: AsyncParser[Msg]

    def __init__(
        self,
        connection: JetStreamContext,
        parser: Optional[AsyncCustomParser[Msg]],
        decoder: Optional[AsyncCustomDecoder[Msg]],
    ):
        self._connection = connection
        self._parser = resolve_custom_func(parser, Parser.parse_message)
        self._decoder = resolve_custom_func(decoder, Parser.decode_message)

    async def publish(
        self,
        message: SendableMessage,
        subject: str,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        stream: Optional[str] = None,
        timeout: Optional[float] = None,
        *,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[DecodedMessage]:
        payload, content_type = encode_message(message)

        headers_to_send = {
            "content-type": content_type or "",
            "correlation_id": correlation_id or str(uuid4()),
            **(headers or {}),
        }
        
        await self._connection.publish(
            subject=subject,
            payload=payload,
            headers=headers_to_send,
            stream=stream,
            timeout=timeout,
        )
