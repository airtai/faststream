from contextlib import asynccontextmanager
from datetime import datetime
from functools import partial
from types import MethodType, TracebackType
from typing import Any, AsyncGenerator, Dict, Optional, Type
from unittest.mock import AsyncMock
from uuid import uuid4

import anyio
from aiokafka import ConsumerRecord

from faststream._compat import override
from faststream.broker.parsers import encode_message
from faststream.broker.test import call_handler, patch_broker_calls
from faststream.kafka.broker import KafkaBroker
from faststream.kafka.producer import AioKafkaFastProducer
from faststream.types import SendableMessage

__all__ = ("TestKafkaBroker",)


class TestKafkaBroker:
    """
    A context manager for creating a test KafkaBroker instance with optional mocking.

    This class serves as a context manager for creating a KafkaBroker instance for testing purposes. It can either use the
    original KafkaBroker instance (if `with_real` is True) or replace certain components with mocks (if `with_real` is
    False) to isolate the broker during testing.

    Args:
        broker (KafkaBroker): The KafkaBroker instance to be used in testing.
        with_real (bool, optional): If True, the original broker is returned; if False, components are replaced with
            mock objects. Defaults to False.

    Attributes:
        broker (KafkaBroker): The KafkaBroker instance provided for testing.
        with_real (bool): A boolean flag indicating whether to use the original broker (True) or replace components with
            mocks (False).

    Methods:
        __aenter__(self) -> KafkaBroker:
            Enter the context and return the KafkaBroker instance.

        __aexit__(self, *args: Any) -> None:
            Exit the context.

    Example usage:

    ```python
    real_broker = KafkaBroker()
    with TestKafkaBroker(real_broker, with_real=True) as broker:
        # Use the real KafkaBroker instance for testing.

    with TestKafkaBroker(real_broker, with_real=False) as broker:
        # Use a mocked KafkaBroker instance for testing.
    """

    # This is set so pytest ignores this class
    __test__ = False

    def __init__(self, broker: KafkaBroker, with_real: bool = False):
        """
        Initialize a TestKafkaBroker instance.

        Args:
            broker (KafkaBroker): The KafkaBroker instance to be used in testing.
            with_real (bool, optional): If True, the original broker is returned; if False, components are replaced with
                mock objects. Defaults to False.
        """
        self.with_real = with_real
        self.broker = broker

    @asynccontextmanager
    async def _create_ctx(self) -> AsyncGenerator[KafkaBroker, None]:
        """
        Create the context for the context manager.

        Yields:
            KafkaBroker: The KafkaBroker instance for testing, either with or without mocks.
        """
        if not self.with_real:
            self.broker.start = AsyncMock(wraps=partial(_fake_start, self.broker))  # type: ignore[method-assign]
            self.broker._connect = MethodType(_fake_connect, self.broker)  # type: ignore[method-assign]
            self.broker.close = MethodType(_fake_close, self.broker)  # type: ignore[method-assign]
        else:
            _fake_start(self.broker)

        async with self.broker:
            try:
                await self.broker.start()
                yield self.broker
            finally:
                pass

    async def __aenter__(self) -> KafkaBroker:
        """
        Enter the context and return the KafkaBroker instance.

        Returns:
            KafkaBroker: The KafkaBroker instance for testing, either with or without mocks.
        """
        self._ctx = self._create_ctx()
        return await self._ctx.__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        """
        Exit the context.

        Args:
            *args: Variable-length argument list.
        """
        await self._ctx.__aexit__(*args)


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
            p._fake_handler = False
            p.mock.reset_mock()

    for h in self.handlers.values():
        for f, _, _, _, _, _ in h.calls:
            f.mock.reset_mock()
            f.event = anyio.Event()


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
        if getattr(p, "_fake_handler", False):
            continue

        handler = self.handlers.get(key)
        if handler is not None:
            for f, _, _, _, _, _ in handler.calls:
                f.mock.side_effect = p.mock
        else:
            p._fake_handler = True

            @self.subscriber(  # type: ignore[call-overload,misc]
                p.topic, batch=p.batch, _raw=True
            )
            def f(msg: Any) -> None:
                pass

            p.mock = f.mock

        p._producer = self._producer

    patch_broker_calls(self)
