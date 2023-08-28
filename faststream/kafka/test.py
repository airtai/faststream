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
    def __init__(self, broker: KafkaBroker):
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
                    message=incoming,
                    rpc=rpc,
                    rpc_timeout=rpc_timeout,
                    raise_timeout=raise_timeout,
                )

                if rpc:  # pragma: no branch
                    return r

        return None


async def _fake_connect(self: KafkaBroker, *args: Any, **kwargs: Any) -> None:
    self._producer = FakeProducer(self)


async def _fake_close(
    self: KafkaBroker,
    exc_type: Optional[Type[BaseException]] = None,
    exc_val: Optional[BaseException] = None,
    exec_tb: Optional[TracebackType] = None,
) -> None:
    for _key, p in self._publishers.items():
        p.mock.reset_mock()
        if getattr(p, "_fake_handler", False):
            self.handlers.pop(p.topic, None)

    for h in self.handlers.values():
        for f, _, _, _, _, _ in h.calls:
            f.mock.reset_mock()
            f.event = None


def _fake_start(self: KafkaBroker, *args: Any, **kwargs: Any) -> None:
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
