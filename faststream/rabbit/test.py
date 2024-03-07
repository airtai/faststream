from typing import TYPE_CHECKING, Any, Optional, Union
from unittest.mock import AsyncMock
from uuid import uuid4

import aiormq
from aio_pika.message import IncomingMessage
from pamqp import commands as spec
from pamqp.header import ContentHeader

from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.test import TestBroker, call_handler
from faststream.rabbit.asyncapi import Publisher
from faststream.rabbit.broker import RabbitBroker
from faststream.rabbit.parser import AioPikaParser
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.rabbit.schemas.constants import ExchangeType
from faststream.rabbit.schemas.schemas import (
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.types import AioPikaSendableMessage
from faststream.types import SendableMessage

if TYPE_CHECKING:
    from aio_pika.abc import DateType, HeadersType, TimeoutType

__all__ = ("TestRabbitBroker",)


class TestRabbitBroker(TestBroker[RabbitBroker]):
    """A class to test RabbitMQ brokers."""

    @classmethod
    def _patch_test_broker(cls, broker: RabbitBroker) -> None:
        broker._channel = AsyncMock()
        broker.declarer = AsyncMock()
        super()._patch_test_broker(broker)

    @staticmethod
    async def _fake_connect(broker: RabbitBroker, *args: Any, **kwargs: Any) -> None:
        broker._producer = FakeProducer(broker)

    @staticmethod
    def patch_publisher(broker: RabbitBroker, publisher: Any) -> None:
        publisher._producer = broker._producer

    @staticmethod
    def create_publisher_fake_subscriber(
        broker: RabbitBroker,
        publisher: Publisher,
    ) -> HandlerCallWrapper[Any, Any, Any]:
        @broker.subscriber(
            queue=publisher.queue,
            exchange=publisher.exchange,
        )
        def f(msg: Any) -> None:
            pass

        return f

    @classmethod
    def _fake_start(cls, broker: RabbitBroker, *args: Any, **kwargs: Any) -> None:
        super()._fake_start(broker, *args, **kwargs)

        for h in broker.handlers.values():
            h.producer = FakeProducer(broker)  # type: ignore[assignment]

    @staticmethod
    def remove_publisher_fake_subscriber(
        broker: RabbitBroker,
        publisher: Publisher,
    ) -> None:
        broker.handlers.pop(
            publisher._get_routing_hash(),
            None,
        )


class PatchedMessage(IncomingMessage):
    """Patched message class for testing purposes.

    This class extends aio_pika's IncomingMessage class and is used to simulate RabbitMQ message handling during tests.
    """

    async def ack(self, multiple: bool = False) -> None:
        """Asynchronously acknowledge a message.

        Args:
            multiple (bool, optional): Whether to acknowledge multiple messages at once. Defaults to False.

        Returns:
            None
        """
        pass

    async def nack(self, multiple: bool = False, requeue: bool = True) -> None:
        """Nack the message.

        Args:
            multiple: Whether to nack multiple messages. Default is False.
            requeue: Whether to requeue the message. Default is True.

        Returns:
            None
        """
        pass

    async def reject(self, requeue: bool = False) -> None:
        """Rejects a task.

        Args:
            requeue: Whether to requeue the task if it fails (default: False)

        Returns:
            None
        """
        pass


def build_message(
    message: AioPikaSendableMessage = "",
    queue: Union[RabbitQueue, str] = "",
    exchange: Union["RabbitExchange", str, None] = None,
    *,
    routing_key: str = "",
    persist: bool = False,
    reply_to: Optional[str] = None,
    headers: Optional["HeadersType"] = None,
    content_type: Optional[str] = None,
    content_encoding: Optional[str] = None,
    priority: Optional[int] = None,
    correlation_id: Optional[str] = None,
    expiration: Optional["DateType"] = None,
    message_id: Optional[str] = None,
    timestamp: Optional["DateType"] = None,
    message_type: Optional[str] = None,
    user_id: Optional[str] = None,
    app_id: Optional[str] = None,
) -> PatchedMessage:
    """Build a patched RabbitMQ message for testing."""
    que = RabbitQueue.validate(queue)
    exch = RabbitExchange.validate(exchange)

    routing = routing_key or que.routing

    msg = AioPikaParser.encode_message(
        message=message,
        persist=persist,
        reply_to=reply_to,
        headers=headers,
        content_type=content_type,
        content_encoding=content_encoding,
        priority=priority,
        correlation_id=correlation_id,
        expiration=expiration,
        message_id=message_id,
        timestamp=timestamp,
        message_type=message_type,
        user_id=user_id,
        app_id=app_id,
    )

    return PatchedMessage(
        aiormq.abc.DeliveredMessage(
            delivery=spec.Basic.Deliver(
                exchange=getattr(exch, "name", ""),
                routing_key=routing,
            ),
            header=ContentHeader(
                properties=spec.Basic.Properties(
                    content_type=msg.content_type,
                    message_id=str(uuid4()),
                    headers=msg.headers,
                    reply_to=reply_to,
                )
            ),
            body=msg.body,
            channel=AsyncMock(),
        )
    )


class FakeProducer(AioPikaFastProducer):
    """A fake RabbitMQ producer for testing purposes.

    This class extends AioPikaFastProducer and is used to simulate RabbitMQ message publishing during tests.
    """

    def __init__(self, broker: RabbitBroker) -> None:
        """Initialize a FakeProducer instance.

        Args:
            broker (RabbitBroker): The RabbitBroker instance to be used for message publishing.
        """
        self.broker = broker

    async def publish(
        self,
        message: AioPikaSendableMessage = "",
        queue: Union[RabbitQueue, str] = "",
        exchange: Union[RabbitExchange, str, None] = None,
        *,
        routing_key: str = "",
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        persist: bool = False,
        reply_to: Optional[str] = None,
        headers: Optional["HeadersType"] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        priority: Optional[int] = None,
        correlation_id: Optional[str] = None,
        expiration: Optional["DateType"] = None,
        message_id: Optional[str] = None,
        timestamp: Optional["DateType"] = None,
        message_type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
        # useless args to be compatible with RabbitBroker.publish()
        mandatory: bool = True,
        immediate: bool = False,
        timeout: "TimeoutType" = None,
    ) -> Optional[SendableMessage]:
        """Publish a message to a RabbitMQ queue or exchange.

        Args:
            message (AioPikaSendableMessage, optional): The message to be published.
            queue (Union[RabbitQueue, str], optional): The target queue for the message.
            exchange (Union[RabbitExchange, str, None], optional): The target exchange for the message.
            routing_key (str, optional): The routing key for the message.
            mandatory (bool, optional): Whether the message is mandatory.
            immediate (bool, optional): Whether the message should be sent immediately.
            timeout (TimeoutType, optional): The timeout for the message.
            rpc (bool, optional): Whether the message is for RPC.
            rpc_timeout (float, optional): The RPC timeout.
            raise_timeout (bool, optional): Whether to raise a timeout exception.
            persist (bool, optional): Whether to persist the message.
            reply_to (str, optional): The reply-to address for RPC messages.
            **message_kwargs (Any): Additional message properties and content.

        Returns:
            Optional[SendableMessage]: The published message if successful, or None if not.
        """
        exch = RabbitExchange.validate(exchange)

        incoming = build_message(
            message=message,
            queue=queue,
            exchange=exch,
            routing_key=routing_key,
            reply_to=reply_to,
            app_id=app_id,
            user_id=user_id,
            message_type=message_type,
            headers=headers,
            persist=persist,
            message_id=message_id,
            priority=priority,
            content_encoding=content_encoding,
            content_type=content_type,
            correlation_id=correlation_id,
            expiration=expiration,
            timestamp=timestamp,
        )

        for handler in self.broker.handlers.values():  # pragma: no branch
            if handler.exchange == exch:
                call: bool = False

                if (
                    handler.exchange is None
                    or handler.exchange.type == ExchangeType.DIRECT
                ):
                    call = handler.queue.name == incoming.routing_key

                elif handler.exchange.type == ExchangeType.FANOUT:
                    call = True

                elif handler.exchange.type == ExchangeType.TOPIC:
                    call = apply_pattern(
                        handler.queue.routing,
                        incoming.routing_key or "",
                    )

                elif handler.exchange.type == ExchangeType.HEADERS:  # pramga: no branch
                    queue_headers = (handler.queue.bind_arguments or {}).copy()
                    msg_headers = incoming.headers

                    if not queue_headers:
                        call = True

                    else:
                        matcher = queue_headers.pop("x-match", "all")

                        full = True
                        none = True
                        for k, v in queue_headers.items():
                            if msg_headers.get(k) != v:
                                full = False
                            else:
                                none = False

                        if not none:
                            call = (matcher == "any") or full

                else:
                    raise AssertionError("unreachable")

                if call:
                    r = await call_handler(
                        handler=handler,
                        message=incoming,
                        rpc=rpc,
                        rpc_timeout=rpc_timeout,
                        raise_timeout=raise_timeout,
                    )

                    if rpc:  # pragma: no branch
                        return r

        return None


def apply_pattern(pattern: str, current: str) -> bool:
    """Apply a pattern to a routing key."""
    pattern_queue = iter(pattern.split("."))
    current_queue = iter(current.split("."))

    pattern_symb = next(pattern_queue, None)
    while pattern_symb:
        if (next_symb := next(current_queue, None)) is None:
            return False

        elif pattern_symb == "#":
            next_pattern = next(pattern_queue, None)

            if next_pattern is None:
                return True

            if (next_symb := next(current_queue, None)) is None:
                return False

            while next_pattern == "*":
                next_pattern = next(pattern_queue, None)
                if (next_symb := next(current_queue, None)) is None:
                    return False

            while next_symb != next_pattern:
                if (next_symb := next(current_queue, None)) is None:
                    return False

            pattern_symb = next(pattern_queue, None)

        elif pattern_symb == "*" or pattern_symb == next_symb:
            pattern_symb = next(pattern_queue, None)

        else:
            return False

    return next(current_queue, None) is None
