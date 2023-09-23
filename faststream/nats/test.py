from contextlib import asynccontextmanager
from functools import partial
from itertools import zip_longest
from types import MethodType, TracebackType
from typing import Any, AsyncGenerator, Dict, Optional, Type, Union
from unittest.mock import AsyncMock
from uuid import uuid4

import anyio
from nats.aio.msg import Msg

from faststream._compat import override
from faststream.broker.parsers import encode_message
from faststream.broker.test import call_handler, patch_broker_calls
from faststream.nats.broker import NatsBroker
from faststream.nats.producer import NatsFastProducer
from faststream.types import DecodedMessage, SendableMessage

__all__ = ("TestNatsBroker",)


class TestNatsBroker:
    # This is set so pytest ignores this class
    __test__ = False

    def __init__(self, broker: NatsBroker, with_real: bool = False):
        self.with_real = with_real
        self.broker = broker

    @asynccontextmanager
    async def _create_ctx(self) -> AsyncGenerator[NatsBroker, None]:
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

    async def __aenter__(self) -> NatsBroker:
        self._ctx = self._create_ctx()
        return await self._ctx.__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        await self._ctx.__aexit__(*args)


class PatchedMessage(Msg):
    async def ack(self) -> None:
        pass

    async def ack_sync(self, timeout: float = 1) -> None:
        pass

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
        _client=None,  # type: ignore
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
    async def publish(
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
    ) -> Optional[DecodedMessage]:
        incoming = build_message(
            message=message,
            subject=subject,
            headers=headers,
            correlation_id=correlation_id,
            reply_to=reply_to,
        )

        for handler in self.broker.handlers.values():  # pragma: no branch
            call = False

            if getattr(handler.stream, "name", None) == stream:
                if subject == handler.subject:
                    call = True

                else:
                    call = True

                    for control, base in zip_longest(
                        subject.split("."),
                        handler.subject.split("."),
                        fillvalue=None,
                    ):
                        if base == ">":
                            break

                        if base != "*" and control != base:
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
    self._js_producer = self._producer = FakeProducer(self)


async def _fake_close(
    self: NatsBroker,
    exc_type: Optional[Type[BaseException]] = None,
    exc_val: Optional[BaseException] = None,
    exec_tb: Optional[TracebackType] = None,
) -> None:
    for p in self._publishers.values():
        p.mock.reset_mock()
        if getattr(p, "_fake_handler", False):
            self.handlers.pop(p.subject, None)
            p._fake_handler = False
            p.mock.reset_mock()

    for h in self.handlers.values():
        for f, _, _, _, _, _ in h.calls:
            f.mock.reset_mock()
            f.event = anyio.Event()


def _fake_start(self: NatsBroker, *args: Any, **kwargs: Any) -> None:
    for key, p in self._publishers.items():
        if getattr(p, "_fake_handler", False):
            continue

        handler = self.handlers.get(key)
        if handler is not None:
            for f, _, _, _, _, _ in handler.calls:
                f.mock.side_effect = p.mock
        else:
            p._fake_handler = True

            @self.subscriber(p.subject, _raw=True)
            def f(msg: Any) -> None:
                pass

            p.mock = f.mock

        p._producer = self._producer

    patch_broker_calls(self)
