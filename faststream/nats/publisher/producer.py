import asyncio
from typing import TYPE_CHECKING, Any, Optional

import anyio
import nats
from typing_extensions import override

from faststream._internal.publisher.proto import ProducerProto
from faststream._internal.subscriber.utils import resolve_custom_func
from faststream.message import encode_message
from faststream.nats.parser import NatsParser

if TYPE_CHECKING:
    from nats.aio.client import Client
    from nats.aio.msg import Msg
    from nats.js import JetStreamContext

    from faststream._internal.types import (
        AsyncCallable,
        CustomCallable,
    )
    from faststream.nats.response import NatsPublishCommand


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
        cmd: "NatsPublishCommand",
    ) -> None:
        payload, content_type = encode_message(cmd.body)

        headers_to_send = {
            "content-type": content_type or "",
            **cmd.headers_to_publish(),
        }

        await self._connection.publish(
            subject=cmd.destination,
            payload=payload,
            reply=cmd.reply_to,
            headers=headers_to_send,
        )

    @override
    async def request(  # type: ignore[override]
        self,
        cmd: "NatsPublishCommand",
    ) -> "Msg":
        payload, content_type = encode_message(cmd.body)

        headers_to_send = {
            "content-type": content_type or "",
            **cmd.headers_to_publish(),
        }

        return await self._connection.request(
            subject=cmd.destination,
            payload=payload,
            headers=headers_to_send,
            timeout=cmd.timeout,
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
        cmd: "NatsPublishCommand",
    ) -> Optional[Any]:
        payload, content_type = encode_message(cmd.body)

        headers_to_send = {
            "content-type": content_type or "",
            **cmd.headers_to_publish(js=True),
        }

        await self._connection.publish(
            subject=cmd.destination,
            payload=payload,
            headers=headers_to_send,
            stream=cmd.stream,
            timeout=cmd.timeout,
        )

        return None

    @override
    async def request(  # type: ignore[override]
        self,
        cmd: "NatsPublishCommand",
    ) -> "Msg":
        payload, content_type = encode_message(cmd.body)

        reply_to = self._connection._nc.new_inbox()
        future: asyncio.Future[Msg] = asyncio.Future()
        sub = await self._connection._nc.subscribe(reply_to, future=future, max_msgs=1)
        await sub.unsubscribe(limit=1)

        headers_to_send = {
            "content-type": content_type or "",
            "reply_to": reply_to,
            **cmd.headers_to_publish(js=False),
        }

        with anyio.fail_after(cmd.timeout):
            await self._connection.publish(
                subject=cmd.destination,
                payload=payload,
                headers=headers_to_send,
                stream=cmd.stream,
                timeout=cmd.timeout,
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
