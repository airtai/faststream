from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, Mapping, Optional, Tuple, Union
from unittest import mock
from unittest.mock import AsyncMock

import aiormq
import anyio
from aio_pika.message import IncomingMessage
from pamqp import commands as spec
from pamqp.header import ContentHeader
from typing_extensions import override

from faststream.broker.message import gen_cor_id
from faststream.broker.utils import resolve_custom_func
from faststream.exceptions import WRONG_PUBLISH_ARGS, SubscriberNotFound
from faststream.rabbit.broker.broker import RabbitBroker
from faststream.rabbit.parser import AioPikaParser
from faststream.rabbit.publisher.asyncapi import AsyncAPIPublisher
from faststream.rabbit.publisher.producer import AioPikaFastProducer
from faststream.rabbit.schemas import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)
from faststream.testing.broker import TestBroker
from faststream.utils.functions import timeout_scope

if TYPE_CHECKING:
    from aio_pika.abc import DateType, HeadersType, TimeoutType

    from faststream.rabbit.subscriber.usecase import LogicSubscriber
    from faststream.rabbit.types import AioPikaSendableMessage


__all__ = ("TestRabbitBroker",)


class TestRabbitBroker(TestBroker[RabbitBroker]):
    """A class to test RabbitMQ brokers."""

    @contextmanager
    def _patch_broker(self, broker: RabbitBroker) -> Generator[None, None, None]:
        with mock.patch.object(
            broker,
            "_channel",
            new_callable=AsyncMock,
        ), mock.patch.object(
            broker,
            "declarer",
            new_callable=AsyncMock,
        ), super()._patch_broker(broker):
            yield

    @staticmethod
    async def _fake_connect(broker: RabbitBroker, *args: Any, **kwargs: Any) -> None:
        broker._producer = FakeProducer(broker)

    @staticmethod
    def create_publisher_fake_subscriber(
        broker: RabbitBroker,
        publisher: AsyncAPIPublisher,
    ) -> Tuple["LogicSubscriber", bool]:
        sub: Optional[LogicSubscriber] = None
        for handler in broker._subscribers.values():
            if _is_handler_suitable(
                handler,
                publisher.routing,
                {},
                publisher.exchange,
            ):
                sub = handler
                break

        if sub is None:
            is_real = False
            sub = broker.subscriber(
                queue=publisher.routing,
                exchange=publisher.exchange,
            )
        else:
            is_real = True

        return sub, is_real


class PatchedMessage(IncomingMessage):
    """Patched message class for testing purposes.

    This class extends aio_pika's IncomingMessage class and is used to simulate RabbitMQ message handling during tests.
    """

    routing_key: str

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
        message_id=message_id or gen_cor_id(),
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
                    headers=msg.headers,
                    reply_to=msg.reply_to,
                    content_encoding=msg.content_encoding,
                    priority=msg.priority,
                    correlation_id=msg.correlation_id,
                    message_id=msg.message_id,
                    timestamp=msg.timestamp,
                    message_type=message_type,
                    user_id=msg.user_id,
                    app_id=msg.app_id,
                )
            ),
            body=msg.body,
            channel=AsyncMock(),
        ),
    )


class FakeProducer(AioPikaFastProducer):
    """A fake RabbitMQ producer for testing purposes.

    This class extends AioPikaFastProducer and is used to simulate RabbitMQ message publishing during tests.
    """

    def __init__(self, broker: RabbitBroker) -> None:
        self.broker = broker

        default_parser = AioPikaParser()
        self._parser = resolve_custom_func(broker._parser, default_parser.parse_message)
        self._decoder = resolve_custom_func(
            broker._decoder, default_parser.decode_message
        )

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "AioPikaSendableMessage",
        exchange: Union["RabbitExchange", str, None] = None,
        *,
        correlation_id: str = "",
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
            if _is_handler_suitable(
                handler, incoming.routing_key, incoming.headers, exch
            ):
                with timeout_scope(rpc_timeout, raise_timeout):
                    response = await self._execute_handler(incoming, handler)
                    if rpc:
                        return await self._decoder(await self._parser(response))

        return None

    @override
    async def request(  # type: ignore[override]
        self,
        message: "AioPikaSendableMessage" = "",
        exchange: Union["RabbitExchange", str, None] = None,
        *,
        correlation_id: str = "",
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: Optional[float] = None,
        persist: bool = False,
        headers: Optional["HeadersType"] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        priority: Optional[int] = None,
        expiration: Optional["DateType"] = None,
        message_id: Optional[str] = None,
        timestamp: Optional["DateType"] = None,
        message_type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> "PatchedMessage":
        """Publish a message to a RabbitMQ queue or exchange."""
        exch = RabbitExchange.validate(exchange)

        incoming = build_message(
            message=message,
            exchange=exch,
            routing_key=routing_key,
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
            if _is_handler_suitable(
                handler, incoming.routing_key, incoming.headers, exch
            ):
                with anyio.fail_after(timeout):
                    return await self._execute_handler(incoming, handler)

        raise SubscriberNotFound

    async def _execute_handler(
        self, msg: PatchedMessage, handler: "LogicSubscriber"
    ) -> "PatchedMessage":
        result = await handler.process_message(msg)

        return build_message(
            routing_key=msg.routing_key,
            message=result.body,
            headers=result.headers,
            correlation_id=result.correlation_id,
        )


def _is_handler_suitable(
    handler: "LogicSubscriber",
    routing_key: str,
    headers: "Mapping[Any, Any]",
    exchange: "RabbitExchange",
) -> bool:
    if handler.exchange != exchange:
        return False

    if handler.exchange is None or handler.exchange.type == ExchangeType.DIRECT:
        return handler.queue.name == routing_key

    elif handler.exchange.type == ExchangeType.FANOUT:
        return True

    elif handler.exchange.type == ExchangeType.TOPIC:
        return apply_pattern(handler.queue.routing, routing_key)

    elif handler.exchange.type == ExchangeType.HEADERS:
        queue_headers = (handler.queue.bind_arguments or {}).copy()

        if not queue_headers:
            return True

        else:
            match_rule = queue_headers.pop("x-match", "all")

            full_match = True
            is_headers_empty = True
            for k, v in queue_headers.items():
                if headers.get(k) != v:
                    full_match = False
                else:
                    is_headers_empty = False

            if is_headers_empty:
                return False

            return full_match or (match_rule == "any")

    raise AssertionError


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
