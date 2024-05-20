from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

from aiokafka import ConsumerRecord
from typing_extensions import override

from faststream.broker.message import encode_message, gen_cor_id
from faststream.kafka import TopicPartition
from faststream.kafka.broker import KafkaBroker
from faststream.kafka.publisher.asyncapi import AsyncAPIBatchPublisher
from faststream.kafka.publisher.producer import AioKafkaFastProducer
from faststream.kafka.subscriber.asyncapi import AsyncAPIBatchSubscriber
from faststream.testing.broker import TestBroker, call_handler

if TYPE_CHECKING:
    from faststream.broker.wrapper.call import HandlerCallWrapper
    from faststream.kafka.publisher.asyncapi import AsyncAPIPublisher
    from faststream.types import SendableMessage

__all__ = ("TestKafkaBroker",)


class TestKafkaBroker(TestBroker[KafkaBroker]):
    """A class to test Kafka brokers."""

    @staticmethod
    async def _fake_connect(  # type: ignore[override]
        broker: KafkaBroker,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[..., AsyncMock]:
        broker._producer = FakeProducer(broker)
        return _fake_connection

    @staticmethod
    def create_publisher_fake_subscriber(
        broker: KafkaBroker,
        publisher: "AsyncAPIPublisher[Any]",
    ) -> "HandlerCallWrapper[Any, Any, Any]":
        if publisher.partition:
            tp = TopicPartition(topic=publisher.topic, partition=publisher.partition)
            sub = broker.subscriber(
                partitions=[tp],
                batch=isinstance(publisher, AsyncAPIBatchPublisher),
            )
        else:
            sub = broker.subscriber(
                publisher.topic,
                batch=isinstance(publisher, AsyncAPIBatchPublisher),
            )

        if not sub.calls:

            @sub  # type: ignore[misc]
            def f(msg: Any) -> None:
                pass

            broker.setup_subscriber(sub)

        return sub.calls[0].handler

    @staticmethod
    def remove_publisher_fake_subscriber(
        broker: KafkaBroker,
        publisher: "AsyncAPIPublisher[Any]",
    ) -> None:
        broker._subscribers.pop(hash(publisher), None)


class FakeProducer(AioKafkaFastProducer):
    """A fake Kafka producer for testing purposes.

    This class extends AioKafkaFastProducer and is used to simulate Kafka message publishing during tests.
    """

    def __init__(self, broker: KafkaBroker) -> None:
        self.broker = broker

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "SendableMessage",
        topic: str,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        *,
        reply_to: str = "",
        rpc: bool = False,
        rpc_timeout: Optional[float] = None,
        raise_timeout: bool = False,
    ) -> Optional[Any]:
        """Publish a message to the Kafka broker."""
        incoming = build_message(
            message=message,
            topic=topic,
            key=key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=headers,
            correlation_id=correlation_id,
            reply_to=reply_to,
        )

        for handler in self.broker._subscribers.values():  # pragma: no branch
            call: bool = False

            for p in handler.partitions:
                if p.topic == topic and (partition is None or p.partition == partition):
                    call = True

            if not call and topic in handler.topics:
                call = True

            if call:
                return await call_handler(
                    handler=handler,
                    message=[incoming]
                    if isinstance(handler, AsyncAPIBatchSubscriber)
                    else incoming,
                    rpc=rpc,
                    rpc_timeout=rpc_timeout,
                    raise_timeout=raise_timeout,
                )

        return None

    async def publish_batch(
        self,
        *msgs: "SendableMessage",
        topic: str,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
    ) -> None:
        """Publish a batch of messages to the Kafka broker."""
        for handler in self.broker._subscribers.values():  # pragma: no branch
            if topic in handler.topics:
                messages = (
                    build_message(
                        message=message,
                        topic=topic,
                        partition=partition,
                        timestamp_ms=timestamp_ms,
                        headers=headers,
                        correlation_id=correlation_id,
                        reply_to=reply_to,
                    )
                    for message in msgs
                )

                if isinstance(handler, AsyncAPIBatchSubscriber):
                    await call_handler(
                        handler=handler,
                        message=list(messages),
                    )

                else:
                    for m in messages:
                        await call_handler(
                            handler=handler,
                            message=m,
                        )
        return None


def build_message(
    message: "SendableMessage",
    topic: str,
    partition: Optional[int] = None,
    timestamp_ms: Optional[int] = None,
    key: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    correlation_id: Optional[str] = None,
    *,
    reply_to: str = "",
) -> ConsumerRecord:
    """Build a Kafka ConsumerRecord for a sendable message."""
    msg, content_type = encode_message(message)

    k = key or b""

    headers = {
        "content-type": content_type or "",
        "correlation_id": correlation_id or gen_cor_id(),
        **(headers or {}),
    }

    if reply_to:
        headers["reply_to"] = headers.get("reply_to", reply_to)

    return ConsumerRecord(
        value=msg,
        topic=topic,
        partition=partition or 0,
        timestamp=timestamp_ms or int(datetime.now().timestamp()),
        timestamp_type=0,
        key=k,
        serialized_key_size=len(k),
        serialized_value_size=len(msg),
        checksum=sum(msg),
        offset=0,
        headers=[(i, j.encode()) for i, j in headers.items()],
    )


def _fake_connection(*args: Any, **kwargs: Any) -> AsyncMock:
    mock = AsyncMock()
    mock.subscribe = MagicMock
    mock.assign = MagicMock
    return mock
