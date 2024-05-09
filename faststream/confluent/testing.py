from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock

from typing_extensions import override

from faststream.broker.message import encode_message, gen_cor_id
from faststream.confluent.broker import KafkaBroker
from faststream.confluent.publisher.asyncapi import AsyncAPIBatchPublisher
from faststream.confluent.publisher.producer import AsyncConfluentFastProducer
from faststream.confluent.subscriber.asyncapi import AsyncAPIBatchSubscriber
from faststream.testing.broker import TestBroker, call_handler

if TYPE_CHECKING:
    from faststream.broker.wrapper.call import HandlerCallWrapper
    from faststream.confluent.publisher.asyncapi import AsyncAPIPublisher
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
        sub = broker.subscriber(  # type: ignore[call-overload,misc]
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


class FakeProducer(AsyncConfluentFastProducer):
    """A fake Kafka producer for testing purposes.

    This class extends AsyncConfluentFastProducer and is used to simulate Kafka message publishing during tests.
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
        correlation_id = correlation_id or gen_cor_id()

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
            if topic in handler.topics:
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
        correlation_id = correlation_id or gen_cor_id()

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


class MockConfluentMessage:
    def __init__(
        self,
        raw_msg: bytes,
        topic: str,
        key: bytes,
        headers: List[Tuple[str, bytes]],
        offset: int,
        partition: int,
        timestamp_type: int,
        timestamp_ms: int,
        error: Optional[str] = None,
    ):
        self._raw_msg = raw_msg
        self._topic = topic
        self._key = key
        self._headers = headers
        self._error = error
        self._offset = offset
        self._partition = partition
        self._timestamp = (timestamp_type, timestamp_ms)

    def len(self) -> int:
        return len(self._raw_msg)

    def error(self) -> Optional[str]:
        return self._error

    def headers(self) -> List[Tuple[str, bytes]]:
        return self._headers

    def key(self) -> bytes:
        return self._key

    def offset(self) -> int:
        return self._offset

    def partition(self) -> int:
        return self._partition

    def timestamp(self) -> Tuple[int, int]:
        return self._timestamp

    def topic(self) -> str:
        return self._topic

    def value(self) -> bytes:
        return self._raw_msg


def build_message(
    message: "SendableMessage",
    topic: str,
    *,
    correlation_id: str,
    partition: Optional[int] = None,
    timestamp_ms: Optional[int] = None,
    key: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    reply_to: str = "",
) -> MockConfluentMessage:
    """Build a mock confluent_kafka.Message for a sendable message."""
    msg, content_type = encode_message(message)
    k = key or b""
    headers = {
        "content-type": content_type or "",
        "correlation_id": correlation_id,
        "reply_to": reply_to,
        **(headers or {}),
    }

    # https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#confluent_kafka.Message.timestamp
    return MockConfluentMessage(
        raw_msg=msg,
        topic=topic,
        key=k,
        headers=[(i, j.encode()) for i, j in headers.items()],
        offset=0,
        partition=partition or 0,
        timestamp_type=0 + 1,
        timestamp_ms=timestamp_ms or int(datetime.now().timestamp()),
    )


def _fake_connection(*args: Any, **kwargs: Any) -> AsyncMock:
    mock = AsyncMock()
    mock.getone.return_value = MagicMock()
    mock.getmany.return_value = [MagicMock()]
    return mock
