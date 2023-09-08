import re
from contextlib import asynccontextmanager
from functools import partial
from types import MethodType, TracebackType
from typing import Any, AsyncGenerator, Optional, Type, Union
from unittest.mock import AsyncMock
from uuid import uuid4

import aiormq
import anyio
from aio_pika.message import IncomingMessage
from pamqp import commands as spec
from pamqp.header import ContentHeader

from faststream.broker.test import call_handler, patch_broker_calls
from faststream.rabbit.broker import RabbitBroker
from faststream.rabbit.message import RabbitMessage
from faststream.rabbit.parser import AioPikaParser
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.rabbit.shared.constants import ExchangeType
from faststream.rabbit.shared.schemas import (
    RabbitExchange,
    RabbitQueue,
    get_routing_hash,
)
from faststream.rabbit.shared.types import TimeoutType
from faststream.rabbit.types import AioPikaSendableMessage
from faststream.types import SendableMessage

__all__ = ("TestRabbitBroker",)


class TestRabbitBroker:

    """
    A context manager for creating a test RabbitBroker instance with optional mocking.

    This class is designed to be used as a context manager for creating a RabbitBroker instance, optionally replacing some
    of its components with mocks for testing purposes. If the `with_real` attribute is set to True, it operates as a
    pass-through context manager, returning the original RabbitBroker instance without any modifications. If `with_real`
    is set to False, it replaces certain components like the channel, declarer, and start/connect/close methods with mock
    objects to isolate the broker for testing.

    Args:
        broker (RabbitBroker): The RabbitBroker instance to be used in testing.
        with_real (bool, optional): If True, the original broker is returned; if False, components are replaced with
            mock objects. Defaults to False.

    Attributes:
        broker (RabbitBroker): The RabbitBroker instance provided for testing.
        with_real (bool): A boolean flag indicating whether to use the original broker (True) or replace components with
            mocks (False).

    Methods:
        __aenter__(self) -> RabbitBroker:
            Enter the context and return the RabbitBroker instance.

        __aexit__(self, *args: Any) -> None:
            Exit the context.

    Example usage:

    ```python
    real_broker = RabbitBroker()
    with TestRabbitBroker(real_broker, with_real=True) as broker:
        # Use the real RabbitBroker instance for testing.

    with TestRabbitBroker(real_broker, with_real=False) as broker:
        # Use a mocked RabbitBroker instance for testing.
    ```
    """

    # This is set so pytest ignores this class
    __test__ = False

    def __init__(self, broker: RabbitBroker, with_real: bool = False):
        """
        Initialize a TestRabbitBroker instance.

        Args:
            broker (RabbitBroker): The RabbitBroker instance to be used in testing.
            with_real (bool, optional): If True, the original broker is returned; if False, components are replaced with
                mock objects. Defaults to False.
        """
        self.with_real = with_real
        self.broker = broker

    @asynccontextmanager
    async def _create_ctx(self) -> AsyncGenerator[RabbitBroker, None]:
        """
        Create the context for the context manager.

        Yields:
            RabbitBroker: The RabbitBroker instance for testing, either with or without mocks.
        """
        if not self.with_real:
            self.broker._channel = AsyncMock()
            self.broker.declarer = AsyncMock()
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

    async def __aenter__(self) -> RabbitBroker:
        """
        Enter the context and return the RabbitBroker instance.

        Returns:
            RabbitBroker: The RabbitBroker instance for testing, either with or without mocks.
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


class PatchedMessage(IncomingMessage):
    """
    Patched message class for testing purposes.

    This class extends aio_pika's IncomingMessage class and is used to simulate RabbitMQ message handling during tests.
    """

    async def ack(self, multiple: bool = False) -> None:
        """Asynchronously acknowledge a message.

        Args:
            multiple (bool, optional): Whether to acknowledge multiple messages at once. Defaults to False.

        Returns:
            None
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
        pass

    async def nack(self, multiple: bool = False, requeue: bool = True) -> None:
        """Nack the message.

        Args:
            multiple: Whether to nack multiple messages. Default is False.
            requeue: Whether to requeue the message. Default is True.

        Returns:
            None
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
        pass

    async def reject(self, requeue: bool = False) -> None:
        """Rejects a task.

        Args:
            requeue: Whether to requeue the task if it fails (default: False)

        Returns:
            None
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
        pass


def build_message(
    message: AioPikaSendableMessage = "",
    queue: Union[RabbitQueue, str] = "",
    exchange: Union[RabbitExchange, str, None] = None,
    *,
    routing_key: str = "",
    reply_to: Optional[str] = None,
    **message_kwargs: Any,
) -> PatchedMessage:
    """
    Build a patched RabbitMQ message for testing.

    Args:
        message (AioPikaSendableMessage): The message content.
        queue (Union[RabbitQueue, str]): The message queue.
        exchange (Union[RabbitExchange, str, None]): The message exchange.
        routing_key (str): The message routing key.
        reply_to (Optional[str]): The reply-to queue.
        **message_kwargs (Any): Additional message arguments.

    Returns:
        PatchedMessage: A patched RabbitMQ message.
    """
    que = RabbitQueue.validate(queue)
    exch = RabbitExchange.validate(exchange)
    msg = AioPikaParser.encode_message(
        message=message,
        persist=False,
        reply_to=reply_to,
        callback_queue=None,
        **message_kwargs,
    )

    routing = routing_key or (que.name if que else "")

    return PatchedMessage(
        aiormq.abc.DeliveredMessage(
            delivery=spec.Basic.Deliver(
                exchange=exch.name if exch and exch.name else "",
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
    """
    A fake RabbitMQ producer for testing purposes.

    This class extends AioPikaFastProducer and is used to simulate RabbitMQ message publishing during tests.
    """

    def __init__(self, broker: RabbitBroker):
        """
        Initialize a FakeProducer instance.

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
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        persist: bool = False,
        reply_to: Optional[str] = None,
        **message_kwargs: Any,
    ) -> Optional[SendableMessage]:
        """
        Publish a message to a RabbitMQ queue or exchange.

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
            **message_kwargs,
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
                    call = bool(
                        re.match(
                            handler.queue.name.replace(".", r"\.").replace("*", ".*"),
                            incoming.routing_key or "",
                        )
                    )

                elif handler.exchange.type == ExchangeType.HEADERS:  # pramga: no branch
                    queue_headers = handler.queue.bind_arguments
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

                else:  # pragma: no cover
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


async def _fake_connect(self: RabbitBroker, *args: Any, **kwargs: Any) -> None:
    """
    Fake connection method for the RabbitBroker class.

    Args:
        self (RabbitBroker): The RabbitBroker instance.
        *args (Any): Additional arguments.
        **kwargs (Any): Additional keyword arguments.
    """
    self._producer = FakeProducer(self)


async def _fake_close(
    self: RabbitBroker,
    exc_type: Optional[Type[BaseException]] = None,
    exc_val: Optional[BaseException] = None,
    exec_tb: Optional[TracebackType] = None,
) -> None:
    """
    Fake close method for the RabbitBroker class.

    Args:
        self (RabbitBroker): The RabbitBroker instance.
        exc_type (Optional[Type[BaseException]]): The exception type.
        exc_val (Optional[BaseException]]): The exception value.
        exec_tb (Optional[TracebackType]]): The exception traceback.
    """
    for key, p in self._publishers.items():
        p.mock.reset_mock()
        if getattr(p, "_fake_handler", False):
            key = get_routing_hash(p.queue, p.exchange)
            self.handlers.pop(key, None)
            p._fake_handler = False
            p.mock.reset_mock()

    for h in self.handlers.values():
        for f, _, _, _, _, _ in h.calls:
            f.mock.reset_mock()
            f.event = anyio.Event()


def _fake_start(self: RabbitBroker, *args: Any, **kwargs: Any) -> None:
    """
    Fake start method for the RabbitBroker class.

    Args:
        self (RabbitBroker): The RabbitBroker instance.
        *args (Any): Additional arguments.
        **kwargs (Any): Additional keyword arguments.
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

            @self.subscriber(
                queue=p.queue,
                exchange=p.exchange,
                _raw=True,
            )
            def f(msg: RabbitMessage) -> str:
                return ""

            p.mock = f.mock

        p._producer = self._producer

    patch_broker_calls(self)
