from typing import Any

import aio_pika

from faststream.broker.message import StreamMessage


class RabbitMessage(StreamMessage[aio_pika.IncomingMessage]):
    """
    A message class for working with RabbitMQ messages.

    This class extends `StreamMessage` to provide additional functionality for acknowledging, rejecting,
    or nack-ing RabbitMQ messages.

    Methods:
        ack(**kwargs) -> None:
            Acknowledge the RabbitMQ message.

        nack(**kwargs) -> None:
            Negative Acknowledgment of the RabbitMQ message.

        reject(**kwargs) -> None:
            Reject the RabbitMQ message.

    """

    async def ack(self, **kwargs: Any) -> None:
        """
        Acknowledge the RabbitMQ message.

        Acknowledgment indicates that the message has been successfully processed.

        Args:
            **kwargs (Any): Additional keyword arguments (not used).

        """
        pika_message = self.raw_message
        if (
            pika_message._IncomingMessage__processed  # type: ignore[attr-defined]
            or pika_message._IncomingMessage__no_ack  # type: ignore[attr-defined]
        ):
            return
        await pika_message.ack()

    async def nack(self, **kwargs: Any) -> None:
        """
        Negative Acknowledgment of the RabbitMQ message.

        Nack-ing a message indicates that the message processing has failed and should be requeued.

        Args:
            **kwargs (Any): Additional keyword arguments (not used).

        """
        pika_message = self.raw_message
        if (
            pika_message._IncomingMessage__processed  # type: ignore[attr-defined]
            or pika_message._IncomingMessage__no_ack  # type: ignore[attr-defined]
        ):
            return
        await pika_message.nack()

    async def reject(self, **kwargs: Any) -> None:
        """
        Reject the RabbitMQ message.

        Rejecting a message indicates that the message processing has failed, and it should not be requeued.

        Args:
            **kwargs (Any): Additional keyword arguments (not used).

        """
        pika_message = self.raw_message
        if (
            pika_message._IncomingMessage__processed  # type: ignore[attr-defined]
            or pika_message._IncomingMessage__no_ack  # type: ignore[attr-defined]
        ):
            return
        await pika_message.reject()
