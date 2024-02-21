from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from typing_extensions import override

from faststream.broker.parsers import encode_message
from faststream.broker.test import TestBroker, call_handler
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.confluent.asyncapi import Publisher
from faststream.confluent.broker import KafkaBroker
from faststream.confluent.producer import AsyncConfluentFastProducer
from faststream.types import SendableMessage

__all__ = ("TestKafkaBroker",)


class TestKafkaBroker(TestBroker[KafkaBroker]):
    """A class to represent a test Kafka broker."""

    @staticmethod
    async def _fake_connect(broker: KafkaBroker, *args: Any, **kwargs: Any) -> None:
        broker._producer = FakeProducer(broker)

    @staticmethod
    def patch_publisher(broker: KafkaBroker, publisher: Any) -> None:
        publisher._producer = broker._producer

    @staticmethod
    def create_publisher_fake_subscriber(
        broker: KafkaBroker,
        publisher: Publisher,
    ) -> HandlerCallWrapper[Any, Any, Any]:
        @broker.subscriber(  # type: ignore[call-overload,misc]
            publisher.topic,
            batch=publisher.batch,
            _raw=True,
        )
        def f(msg: Any) -> None:
            pass

        return f  # type: ignore[no-any-return]

    @staticmethod
    def remove_publisher_fake_subscriber(
        broker: KafkaBroker, publisher: Publisher
    ) -> None:
        broker.handlers.pop(publisher.topic, None)


class FakeProducer(AsyncConfluentFastProducer):
    """A fake Kafka producer for testing purposes.

    This class extends AsyncConfluentFastProducer and is used to simulate Kafka message publishing during tests.
    """

    def __init__(self, broker: KafkaBroker) -> None:
        """Initialize the FakeProducer.

        Args:
            broker (KafkaBroker): The KafkaBroker instance to associate with this FakeProducer.
        """
        self.broker = broker

    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
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
    ) -> Optional[SendableMessage]:
        """Publish a message to the Kafka broker.

        Args:
            message (SendableMessage): The message to be published.
            topic (str): The Kafka topic to publish the message to.
            key (Optional[bytes], optional): The message key. Defaults to None.
            partition (Optional[int], optional): The Kafka partition to use. Defaults to None.
            timestamp_ms (Optional[int], optional): The message timestamp in milliseconds. Defaults to None.
            headers (Optional[Dict[str, str]], optional): Additional headers for the message. Defaults to None.
            correlation_id (Optional[str], optional): The correlation ID for the message. Defaults to None.
            reply_to (str, optional): The topic to which responses should be sent. Defaults to "".
            rpc (bool, optional): If True, treat the message as an RPC request. Defaults to False.
            rpc_timeout (Optional[float], optional): Timeout for RPC requests. Defaults to None.
            raise_timeout (bool, optional): If True, raise an exception on timeout. Defaults to False.

        Returns:
            Optional[SendableMessage]: The response message, if this was an RPC request, otherwise None.
        """
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

        for handler in self.broker.handlers.values():  # pragma: no branch
            if topic in handler.topics:
                return await call_handler(
                    handler=handler,
                    message=[incoming] if handler.batch else incoming,
                    rpc=rpc,
                    rpc_timeout=rpc_timeout,
                    raise_timeout=raise_timeout,
                )

        return None

    async def publish_batch(
        self,
        *msgs: SendableMessage,
        topic: str,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Publish a batch of messages to the Kafka broker.

        Args:
            *msgs (SendableMessage): Variable number of messages to be published.
            topic (str): The Kafka topic to publish the messages to.
            partition (Optional[int], optional): The Kafka partition to use. Defaults to None.
            timestamp_ms (Optional[int], optional): The message timestamp in milliseconds. Defaults to None.
            headers (Optional[Dict[str, str]], optional): Additional headers for the messages. Defaults to None.

        Returns:
            None: This method does not return a value.
        """
        for handler in self.broker.handlers.values():  # pragma: no branch
            if topic in handler.topics:
                await call_handler(
                    handler=handler,
                    message=[
                        build_message(
                            message=message,
                            topic=topic,
                            partition=partition,
                            timestamp_ms=timestamp_ms,
                            headers=headers,
                        )
                        for message in msgs
                    ],
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
    message: SendableMessage,
    topic: str,
    partition: Optional[int] = None,
    timestamp_ms: Optional[int] = None,
    key: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    correlation_id: Optional[str] = None,
    *,
    reply_to: str = "",
) -> MockConfluentMessage:
    """Build a mock confluent_kafka.Message for a sendable message.

    Args:
        message (SendableMessage): The sendable message to be encoded.
        topic (str): The Kafka topic for the message.
        partition (Optional[int], optional): The Kafka partition for the message. Defaults to None.
        timestamp_ms (Optional[int], optional): The message timestamp in milliseconds. Defaults to None.
        key (Optional[bytes], optional): The message key. Defaults to None.
        headers (Optional[Dict[str, str]], optional): Additional headers for the message. Defaults to None.
        correlation_id (Optional[str], optional): The correlation ID for the message. Defaults to None.
        reply_to (str, optional): The topic to which responses should be sent. Defaults to "".

    Returns:
        MockConfluentMessage: A mock confluent_kafka.Message object.
    """
    msg, content_type = encode_message(message)
    k = key or b""
    headers = {
        "content-type": content_type or "",
        "correlation_id": correlation_id or str(uuid4()),
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
