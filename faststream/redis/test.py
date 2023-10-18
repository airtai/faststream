from typing import Any, Optional

from faststream._compat import override
from faststream.broker.test import TestBroker, call_handler
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.redis.asyncapi import Handler, Publisher
from faststream.redis.broker import RedisBroker
from faststream.redis.message import PubSubMessage
from faststream.redis.parser import RawMessage
from faststream.redis.producer import RedisFastProducer
from faststream.types import AnyDict, DecodedMessage, SendableMessage

__all__ = ("TestRedisBroker",)


class TestRedisBroker(TestBroker[RedisBroker]):
    @staticmethod
    def patch_publisher(
        broker: RedisBroker,
        publisher: Any,
    ) -> None:
        publisher._producer = broker._producer

    @staticmethod
    def create_publisher_fake_subscriber(
        broker: RedisBroker,
        publisher: Publisher,
    ) -> HandlerCallWrapper[Any, Any, Any]:
        @broker.subscriber(
            publisher.channel,
            _raw=True,
        )
        def f(msg: Any) -> None:
            pass

        return f

    @staticmethod
    async def _fake_connect(
        broker: RedisBroker,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        broker._producer = FakeProducer(broker)  # type: ignore[assignment]

    @staticmethod
    def remove_publisher_fake_subscriber(
        broker: RedisBroker,
        publisher: Publisher,
    ) -> None:
        broker.handlers.pop(Handler.get_routing_hash(publisher.channel), None)


class FakeProducer(RedisFastProducer):
    def __init__(self, broker: RedisBroker):
        self.broker = broker

    @override
    async def publish(
        self,
        message: SendableMessage,
        channel: str,
        reply_to: str = "",
        headers: Optional[AnyDict] = None,
        correlation_id: Optional[str] = None,
        *,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[DecodedMessage]:
        incoming = build_message(
            message=message,
            channel=channel,
            headers=headers,
            correlation_id=correlation_id,
            reply_to=reply_to,
        )

        for handler in self.broker.handlers.values():  # pragma: no branch
            call = False

            if channel == handler.channel:
                call = True

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


def build_message(
    message: SendableMessage,
    channel: str,
    *,
    reply_to: str = "",
    correlation_id: Optional[str] = None,
    headers: Optional[AnyDict] = None,
) -> PubSubMessage:
    data = RawMessage.encode(
        message=message,
        reply_to=reply_to,
        headers=headers,
        correlation_id=correlation_id,
    )
    return PubSubMessage(
        channel=channel.encode(),
        data=data.encode(),
        type="message",
    )
