from contextlib import asynccontextmanager
from functools import partial
from itertools import zip_longest
from types import MethodType, TracebackType
from typing import Any, AsyncGenerator, Dict, Optional, Type, Union
from unittest.mock import AsyncMock
from uuid import uuid4

from nats.aio.msg import Msg

from faststream._compat import override
from faststream.broker.middlewares import CriticalLogMiddleware
from faststream.broker.parsers import encode_message
from faststream.broker.test import call_handler, patch_broker_calls
from faststream.nats.asyncapi import Handler
from faststream.nats.broker import NatsBroker
from faststream.nats.producer import NatsFastProducer
from faststream.types import SendableMessage

__all__ = ("TestNatsBroker",)


class TestNatsBroker:
    # This is set so pytest ignores this class
    __test__ = False

    def __init__(
        self,
        broker: NatsBroker,
        with_real: bool = False,
        connect_only: bool = False,
    ):
        self.with_real = with_real
        self.broker = broker
        self.connect_only = connect_only

    @asynccontextmanager
    async def _create_ctx(self) -> AsyncGenerator[NatsBroker, None]:
        if not self.with_real:
            self.broker.start = AsyncMock(wraps=partial(_fake_start, self.broker))  # type: ignore[method-assign]
            self.broker._connect = MethodType(_fake_connect, self.broker)  # type: ignore[method-assign]
            self.broker.close = AsyncMock()  # type: ignore[method-assign]
        else:
            _fake_start(self.broker)

        async with self.broker:
            try:
                if not self.connect_only:
                    await self.broker.start()
                yield self.broker
            finally:
                _fake_close(self.broker)

    async def __aenter__(self) -> NatsBroker:
        self._ctx = self._create_ctx()
        return await self._ctx.__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        await self._ctx.__aexit__(*args)


class PatchedMessage(Msg):
    async def ack(self) -> None:
        pass

    async def ack_sync(self, timeout: float = 1) -> "PatchedMessage":
        return self

    async def nak(self, delay: Union[int, float, None] = None) -> None:
        pass

    async def term(self) -> None:
        pass

    async def in_progress(self) -> None:
        pass


def build_message(
    message: SendableMessage,
    subject: str,
    *,
    reply_to: str = "",
    correlation_id: Optional[str] = None,
    headers: Optional[Dict[str, Any]] = None,
) -> PatchedMessage:
    msg, content_type = encode_message(message)
    return PatchedMessage(
        _client=None,  # type: ignore[arg-type]
        subject=subject,
        reply=reply_to,
        data=msg,
        headers={
            "content-type": content_type or "",
            "correlation_id": correlation_id or str(uuid4()),
            **(headers or {}),
        },
    )


class FakeProducer(NatsFastProducer):
    def __init__(self, broker: NatsBroker):
        self.broker = broker

    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
        subject: str,
        reply_to: str = "",
        headers: Optional[Dict[str, str]] = None,
        stream: Optional[str] = None,
        correlation_id: Optional[str] = None,
        *,
        rpc: bool = False,
        rpc_timeout: Optional[float] = None,
        raise_timeout: bool = False,
    ) -> Optional[SendableMessage]:
        incoming = build_message(
            message=message,
            subject=subject,
            headers=headers,
            correlation_id=correlation_id,
            reply_to=reply_to,
        )

        for handler in self.broker.handlers.values():  # pragma: no branch
            call = False

            if subject == handler.subject:
                call = True

            else:
                call = True

                for current, base in zip_longest(
                    subject.split("."),
                    handler.subject.split("."),
                    fillvalue=None,
                ):
                    if base == ">":
                        break

                    if base != "*" and current != base:
                        call = False
                        break

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


async def _fake_connect(self: NatsBroker, *args: Any, **kwargs: Any) -> None:
    self._js_producer = self._producer = FakeProducer(self)  # type: ignore[assignment]


def _fake_close(
    broker: NatsBroker,
    exc_type: Optional[Type[BaseException]] = None,
    exc_val: Optional[BaseException] = None,
    exec_tb: Optional[TracebackType] = None,
) -> None:
    broker.middlewares = [
        CriticalLogMiddleware(broker.logger, broker.log_level),
        *broker.middlewares,
    ]

    for p in broker._publishers.values():
        p.mock.reset_mock()
        if getattr(p, "_fake_handler", False):
            broker.handlers.pop(Handler.get_routing_hash(p.subject), None)
            p._fake_handler = False
            p.mock.reset_mock()

    for h in broker.handlers.values():
        for f, _, _, _, _, _ in h.calls:
            f.refresh(with_mock=True)


def _fake_start(broker: NatsBroker, *args: Any, **kwargs: Any) -> None:
    for key, p in broker._publishers.items():
        if getattr(p, "_fake_handler", False):
            continue

        handler = broker.handlers.get(key)
        if handler is not None:
            for f, _, _, _, _, _ in handler.calls:
                f.mock.side_effect = p.mock
        else:
            p._fake_handler = True

            @broker.subscriber(p.subject, _raw=True)
            def f(msg: Any) -> None:
                pass

            p.mock = f.mock

        p._producer = broker._producer

    patch_broker_calls(broker)
