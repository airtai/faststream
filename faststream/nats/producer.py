import asyncio
from secrets import token_hex
from typing import Any, Dict, Optional
from uuid import uuid4

import nats
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js import JetStreamContext

from faststream.broker.parsers import encode_message, resolve_custom_func
from faststream.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    AsyncDecoder,
    AsyncParser,
)
from faststream.exceptions import WRONG_PUBLISH_ARGS
from faststream.nats.message import NatsMessage
from faststream.nats.parser import Parser
from faststream.types import DecodedMessage, SendableMessage
from faststream.utils.functions import timeout_scope


class NatsFastProducer:
    _connection: Client
    _decoder: AsyncDecoder[Any]
    _parser: AsyncParser[Msg, Any]

    def __init__(
        self,
        connection: Client,
        parser: Optional[AsyncCustomParser[Msg, NatsMessage]],
        decoder: Optional[AsyncCustomDecoder[NatsMessage]],
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
            msg: Any = None
            with timeout_scope(rpc_timeout, raise_timeout):
                msg = await future

            if msg:  # pragma: no branch
                if msg.headers:  # pragma: no cover
                    if (
                        msg.headers.get(nats.js.api.Header.STATUS)
                        == nats.aio.client.NO_RESPONDERS_STATUS
                    ):
                        raise nats.errors.NoRespondersError
                return await self._decoder(await self._parser(msg))

        return None


class NatsJSFastProducer:
    _connection: JetStreamContext
    _decoder: AsyncDecoder[Any]
    _parser: AsyncParser[Msg, Any]

    def __init__(
        self,
        connection: JetStreamContext,
        parser: Optional[AsyncCustomParser[Msg, NatsMessage]],
        decoder: Optional[AsyncCustomDecoder[NatsMessage]],
    ):
        self._connection = connection
        self._parser = resolve_custom_func(parser, Parser.parse_message)
        self._decoder = resolve_custom_func(decoder, Parser.decode_message)

    async def publish(
        self,
        message: SendableMessage,
        subject: str,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
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

        if rpc:
            if reply_to:
                raise WRONG_PUBLISH_ARGS

            reply_to = str(uuid4())
            future: asyncio.Future[Msg] = asyncio.Future()
            sub = await self._connection._nc.subscribe(
                reply_to, future=future, max_msgs=1
            )
            await sub.unsubscribe(limit=1)

        if reply_to:
            headers_to_send.update({"reply_to": reply_to})

        await self._connection.publish(
            subject=subject,
            payload=payload,
            headers=headers_to_send,
            stream=stream,
            timeout=timeout,
        )

        if rpc:
            msg: Any = None
            with timeout_scope(rpc_timeout, raise_timeout):
                msg = await future

            if msg:  # pragma: no branch
                if msg.headers:  # pragma: no cover
                    if (
                        msg.headers.get(nats.js.api.Header.STATUS)
                        == nats.aio.client.NO_RESPONDERS_STATUS
                    ):
                        raise nats.errors.NoRespondersError
                return await self._decoder(await self._parser(msg))

        return None
