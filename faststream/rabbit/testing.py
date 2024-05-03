from typing import TYPE_CHECKING, Any, Optional, Union
from unittest.mock import AsyncMock

import aiormq
from aio_pika.message import IncomingMessage
from pamqp import commands as spec
from pamqp.header import ContentHeader
from typing_extensions import override

from faststream.broker.message import gen_cor_id
from faststream.exceptions import WRONG_PUBLISH_ARGS
from faststream.rabbit.broker.broker import RabbitBroker
from faststream.rabbit.parser import AioPikaParser
from faststream.rabbit.publisher.asyncapi import AsyncAPIPublisher
from faststream.rabbit.publisher.producer import AioPikaFastProducer
from faststream.rabbit.schemas import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.subscriber.asyncapi import AsyncAPISubscriber
from faststream.testing.broker import TestBroker, call_handler

if TYPE_CHECKING:
    from aio_pika.abc import DateType, HeadersType, TimeoutType

    from faststream.broker.wrapper.call import HandlerCallWrapper
    from faststream.rabbit.types import AioPikaSendableMessage

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
    def create_publisher_fake_subscriber(
        broker: RabbitBroker,
        publisher: AsyncAPIPublisher,
    ) -> "HandlerCallWrapper[Any, Any, Any]":
        sub = broker.subscriber(
            queue=publisher.queue,
            exchange=publisher.exchange,
        )

        if not sub.calls:

            @sub
            def f(msg: Any) -> None:
                pass

            broker.setup_subscriber(sub)

        return sub.calls[0].handler

    @staticmethod
    def remove_publisher_fake_subscriber(
        broker: RabbitBroker,
        publisher: AsyncAPIPublisher,
    ) -> None:
        broker._subscribers.pop(
            AsyncAPISubscriber.get_routing_hash(
                queue=publisher.queue,
                exchange=publisher.exchange,
            ),
            None,
        )


class PatchedMessage(IncomingMessage):
    """Patched message class for testing purposes.

    This class extends aio_pika's IncomingMessage class and is used to simulate RabbitMQ message handling during tests.
    """

    async def ack(self, multiple: bool = False) -> None:
        """Asynchronously acknowledge a message."""
        pass

    async def nack(self, multiple: bool = False, requeue: bool = True) -> None:
        """Nack the message."""
        pass

    async def reject(self, requeue: bool = False) -> None:
        """Rejects a task."""
        pass


def build_message(
    message: "AioPikaSendableMessage" = "",
    queue: Union["RabbitQueue", str] = "",
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
                    message_id=gen_cor_id(),
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
        self.broker = broker

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "AioPikaSendableMessage" = "",
        exchange: Union["RabbitExchange", str, None] = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: "TimeoutType" = None,
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
    ) -> Optional[Any]:
        """Publish a message to a RabbitMQ queue or exchange."""
        exch = RabbitExchange.validate(exchange)

        if rpc and reply_to:
            raise WRONG_PUBLISH_ARGS

        incoming = build_message(
            message=message,
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

        for handler in self.broker._subscribers.values():  # pragma: no branch
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
