from typing import Any

import aio_pika

from faststream.broker.message import StreamMessage


class RabbitMessage(StreamMessage[aio_pika.IncomingMessage]):
    async def ack(self, **kwargs: Any) -> None:
        pika_message = self.raw_message
        if (
            pika_message._IncomingMessage__processed  # type: ignore[attr-defined]
            or pika_message._IncomingMessage__no_ack  # type: ignore[attr-defined]
        ):
            return
        await pika_message.ack()

    async def nack(self, **kwargs: Any) -> None:
        pika_message = self.raw_message
        if (
            pika_message._IncomingMessage__processed  # type: ignore[attr-defined]
            or pika_message._IncomingMessage__no_ack  # type: ignore[attr-defined]
        ):
            return
        await pika_message.nack()

    async def reject(self, **kwargs: Any) -> None:
        pika_message = self.raw_message
        if (
            pika_message._IncomingMessage__processed  # type: ignore[attr-defined]
            or pika_message._IncomingMessage__no_ack  # type: ignore[attr-defined]
        ):
            return
        await pika_message.reject()
