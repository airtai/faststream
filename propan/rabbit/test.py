import re
from functools import partial
from types import MethodType, TracebackType
from typing import Any, Optional, Type, Union
from unittest.mock import AsyncMock
from uuid import uuid4

import aiormq
from aio_pika.message import IncomingMessage
from pamqp import commands as spec
from pamqp.header import ContentHeader

from propan.broker.test import call_handler, patch_broker_calls
from propan.rabbit.broker import RabbitBroker
from propan.rabbit.message import RabbitMessage
from propan.rabbit.parser import AioPikaParser
from propan.rabbit.producer import AioPikaPropanProducer
from propan.rabbit.shared.constants import ExchangeType
from propan.rabbit.shared.schemas import RabbitExchange, RabbitQueue, get_routing_hash
from propan.rabbit.shared.types import TimeoutType
from propan.rabbit.types import AioPikaSendableMessage
from propan.types import SendableMessage

__all__ = ("TestRabbitBroker",)


def TestRabbitBroker(broker: RabbitBroker, with_real: bool = False) -> RabbitBroker:
    if with_real:
        return broker

    broker._channel = AsyncMock()
    broker.declarer = AsyncMock()
    _fake_start(broker)
    broker.start = AsyncMock(wraps=partial(_fake_start, broker))  # type: ignore[method-assign]
    broker._connect = MethodType(_fake_connect, broker)  # type: ignore[method-assign]
    broker.close = MethodType(_fake_close, broker)  # type: ignore[method-assign]
    return broker


class PatchedMessage(IncomingMessage):
    async def ack(self, multiple: bool = False) -> None:
        pass

    async def nack(self, multiple: bool = False, requeue: bool = True) -> None:
        pass

    async def reject(self, requeue: bool = False) -> None:
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


class FakeProducer(AioPikaPropanProducer):
    def __init__(self, broker: RabbitBroker):
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
    self._producer = FakeProducer(self)


async def _fake_close(
    self: RabbitBroker,
    exc_type: Optional[Type[BaseException]] = None,
    exc_val: Optional[BaseException] = None,
    exec_tb: Optional[TracebackType] = None,
) -> None:
    for key, p in self._publishers.items():
        p.mock.reset_mock()
        if getattr(p, "_fake_handler", False):
            key = get_routing_hash(p.queue, p.exchange)
            self.handlers.pop(key, None)

    for h in self.handlers.values():
        for f, _, _, _, _, _ in h.calls:
            f.mock.reset_mock()


def _fake_start(self: RabbitBroker, *args: Any, **kwargs: Any) -> None:
    for key, p in self._publishers.items():
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
