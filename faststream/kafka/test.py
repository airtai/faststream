from datetime import datetime
from functools import partial
from types import MethodType, TracebackType
from typing import Any, Dict, Optional, Type
from unittest.mock import AsyncMock
from uuid import uuid4

from aiokafka import ConsumerRecord

from faststream._compat import override
from faststream.broker.parsers import encode_message
from faststream.broker.test import call_handler, patch_broker_calls
from faststream.kafka.broker import KafkaBroker
from faststream.kafka.message import KafkaMessage
from faststream.kafka.producer import AioKafkaFastProducer
from faststream.types import SendableMessage

__all__ = ("TestKafkaBroker",)


def TestKafkaBroker(broker: KafkaBroker, with_real: bool = False) -> KafkaBroker:
    """
    Create a test instance of a KafkaBroker.

    Args:
        broker (KafkaBroker): The KafkaBroker instance to use.
        with_real (bool, optional): If True, use the real broker, otherwise use a test version. Defaults to False.

    Returns:
        KafkaBroker: The KafkaBroker instance for testing.
    """
    if with_real:
        return broker
    _fake_start(broker)
    broker.start = AsyncMock(wraps=partial(_fake_start, broker))  # type: ignore[method-assign]
    broker._connect = MethodType(_fake_connect, broker)  # type: ignore[method-assign]
    broker.close = MethodType(_fake_close, broker)  # type: ignore[method-assign]
    return broker


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
) -> ConsumerRecord:
    """
    Build a Kafka ConsumerRecord for a sendable message.

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
        ConsumerRecord: A Kafka ConsumerRecord object.
    """
    msg, content_type = encode_message(message)
    k = key or b""
    headers = {
        "content-type": content_type or "",
        "correlation_id": correlation_id or str(uuid4()),
        "reply_to": reply_to,
        **(headers or {}),
    }

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


class FakeProducer(AioKafkaFastProducer):
    """
    A fake Kafka producer for testing purposes.

    This class extends AioKafkaFastProducer and is used to simulate Kafka message publishing during tests.
    """
    def __init__(self, broker: KafkaBroker):
        """
        Initialize the FakeProducer.

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
        """
        Publish a message to the Kafka broker.

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
                r = await call_handler(
                    handler=handler,
                    message=[incoming] if handler.batch else incoming,
                    rpc=rpc,
                    rpc_timeout=rpc_timeout,
                    raise_timeout=raise_timeout,
                )

                if rpc:  # pragma: no branch
                    return r

        return None

    async def publish_batch(
        self,
        *msgs: SendableMessage,
        topic: str,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Publish a batch of messages to the Kafka broker.

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


async def _fake_connect(self: KafkaBroker, *args: Any, **kwargs: Any) -> None:
    """
    Fake connection to Kafka.

    Args:
        self (KafkaBroker): The KafkaBroker instance.
        *args (Any): Additional arguments.
        **kwargs (Any): Additional keyword arguments.

    Returns:
        None: This method does not return a value.
    """
    self._producer = FakeProducer(self)


async def _fake_close(
    self: KafkaBroker,
    exc_type: Optional[Type[BaseException]] = None,
    exc_val: Optional[BaseException] = None,
    exec_tb: Optional[TracebackType] = None,
) -> None:
    """
    Fake closing of the KafkaBroker.

    Args:
        self (KafkaBroker): The KafkaBroker instance.
        exc_type (Optional[Type[BaseException]], optional): Exception type. Defaults to None.
        exc_val (Optional[BaseException], optional): Exception value. Defaults to None.
        exec_tb (Optional[TracebackType], optional): Traceback information. Defaults to None.

    Returns:
        None: This method does not return a value.
    """
    for p in self._publishers.values():
        p.mock.reset_mock()
        if getattr(p, "_fake_handler", False):
            self.handlers.pop(p.topic, None)

    for h in self.handlers.values():
        for f, _, _, _, _, _ in h.calls:
            f.mock.reset_mock()
            f.event = None


def _fake_start(self: KafkaBroker, *args: Any, **kwargs: Any) -> None:
    """
    Fake starting of the KafkaBroker.

    Args:
        self (KafkaBroker): The KafkaBroker instance.
        *args (Any): Additional arguments.
        **kwargs (Any): Additional keyword arguments.

    Returns:
        None: This method does not return a value.
    """
    for key, p in self._publishers.items():
        handler = self.handlers.get(key)

        if handler is not None:
            for f, _, _, _, _, _ in handler.calls:
                f.mock.side_effect = p.mock

        else:
            p._fake_handler = True

            @self.subscriber(p.topic, _raw=True)
            def f(msg: KafkaMessage) -> str:
                return ""

            p.mock = f.mock

        p._producer = self._producer

    patch_broker_calls(self)
