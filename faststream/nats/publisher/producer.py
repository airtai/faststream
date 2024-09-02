import asyncio
from typing import TYPE_CHECKING, Any, Dict, Optional

import anyio
import nats
from typing_extensions import override

from faststream.broker.message import encode_message
from faststream.broker.publisher.proto import ProducerProto
from faststream.broker.utils import resolve_custom_func
from faststream.exceptions import WRONG_PUBLISH_ARGS
from faststream.nats.parser import NatsParser
from faststream.utils.functions import timeout_scope

if TYPE_CHECKING:
    from nats.aio.client import Client
    from nats.aio.msg import Msg
    from nats.js import JetStreamContext

    from faststream.broker.types import (
        AsyncCallable,
        CustomCallable,
    )
    from faststream.types import SendableMessage


class NatsFastProducer(ProducerProto):
    """A class to represent a NATS producer."""

    _decoder: "AsyncCallable"
    _parser: "AsyncCallable"

    def __init__(
        self,
        *,
        connection: "Client",
        parser: Optional["CustomCallable"],
        decoder: Optional["CustomCallable"],
    ) -> None:
        self._connection = connection

        default = NatsParser(pattern="", no_ack=False)
        self._parser = resolve_custom_func(parser, default.parse_message)
        self._decoder = resolve_custom_func(decoder, default.decode_message)

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "SendableMessage",
        subject: str,
        *,
        correlation_id: str,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        **kwargs: Any,  # suprress stream option
    ) -> Optional[Any]:
        payload, content_type = encode_message(message)

        headers_to_send = {
            "content-type": content_type or "",
            "correlation_id": correlation_id,
            **(headers or {}),
        }

        client = self._connection

        if rpc:
            if reply_to:
                raise WRONG_PUBLISH_ARGS

            reply_to = client.new_inbox()

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
                if msg.headers:  # pragma: no cover # noqa: SIM102
                    if (
                        msg.headers.get(nats.js.api.Header.STATUS)
                        == nats.aio.client.NO_RESPONDERS_STATUS
                    ):
                        raise nats.errors.NoRespondersError
                return await self._decoder(await self._parser(msg))

        return None

    @override
    async def request(  # type: ignore[override]
        self,
        message: "SendableMessage",
        subject: str,
        *,
        correlation_id: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 0.5,
    ) -> "Msg":
        payload, content_type = encode_message(message)

        headers_to_send = {
            "content-type": content_type or "",
            "correlation_id": correlation_id,
            **(headers or {}),
        }

        return await self._connection.request(
            subject=subject,
            payload=payload,
            headers=headers_to_send,
            timeout=timeout,
        )


class NatsJSFastProducer(ProducerProto):
    """A class to represent a NATS JetStream producer."""

    _decoder: "AsyncCallable"
    _parser: "AsyncCallable"

    def __init__(
        self,
        *,
        connection: "JetStreamContext",
        parser: Optional["CustomCallable"],
        decoder: Optional["CustomCallable"],
    ) -> None:
        self._connection = connection

        default = NatsParser(pattern="", no_ack=False)
        self._parser = resolve_custom_func(parser, default.parse_message)
        self._decoder = resolve_custom_func(decoder, default.decode_message)

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "SendableMessage",
        subject: str,
        *,
        correlation_id: str,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        stream: Optional[str] = None,
        timeout: Optional[float] = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[Any]:
        payload, content_type = encode_message(message)

        headers_to_send = {
            "content-type": content_type or "",
            "correlation_id": correlation_id,
            **(headers or {}),
        }

        if rpc:
            if reply_to:
                raise WRONG_PUBLISH_ARGS
            reply_to = self._connection._nc.new_inbox()
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
                if msg.headers:  # pragma: no cover # noqa: SIM102
                    if (
                        msg.headers.get(nats.js.api.Header.STATUS)
                        == nats.aio.client.NO_RESPONDERS_STATUS
                    ):
                        raise nats.errors.NoRespondersError
                return await self._decoder(await self._parser(msg))

        return None

    @override
    async def request(  # type: ignore[override]
        self,
        message: "SendableMessage",
        subject: str,
        *,
        correlation_id: str,
        headers: Optional[Dict[str, str]] = None,
        stream: Optional[str] = None,
        timeout: float = 0.5,
    ) -> "Msg":
        payload, content_type = encode_message(message)

        reply_to = self._connection._nc.new_inbox()
        future: asyncio.Future[Msg] = asyncio.Future()
        sub = await self._connection._nc.subscribe(reply_to, future=future, max_msgs=1)
        await sub.unsubscribe(limit=1)

        headers_to_send = {
            "content-type": content_type or "",
            "correlation_id": correlation_id,
            "reply_to": reply_to,
            **(headers or {}),
        }

        with anyio.fail_after(timeout):
            await self._connection.publish(
                subject=subject,
                payload=payload,
                headers=headers_to_send,
                stream=stream,
                timeout=timeout,
            )

            msg = await future

            if (  # pragma: no cover
                msg.headers
                and (
                    msg.headers.get(nats.js.api.Header.STATUS)
                    == nats.aio.client.NO_RESPONDERS_STATUS
                )
            ):
                raise nats.errors.NoRespondersError

            return msg
