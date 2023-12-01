import re
from typing import Any, Optional

from faststream._compat import override
from faststream.broker.test import TestBroker, call_handler
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.redis.asyncapi import Handler, Publisher
from faststream.redis.broker import RedisBroker
from faststream.redis.message import AnyRedisDict
from faststream.redis.parser import RawMessage
from faststream.redis.producer import RedisFastProducer
from faststream.redis.schemas import INCORRECT_SETUP_MSG
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
            channel=publisher.channel,
            list=publisher.list,
            stream=publisher.stream,
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
        any_of = publisher.channel or publisher.list or publisher.stream
        assert any_of  # nosec B101
        broker.handlers.pop(Handler.get_routing_hash(any_of), None)


class FakeProducer(RedisFastProducer):
    def __init__(self, broker: RedisBroker):
        self.broker = broker

    @override
    async def publish(
        self,
        message: SendableMessage,
        channel: Optional[str] = None,
        reply_to: str = "",
        headers: Optional[AnyDict] = None,
        correlation_id: Optional[str] = None,
        *,
        list: Optional[str] = None,
        stream: Optional[str] = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[DecodedMessage]:
        any_of = channel or list or stream
        if any_of is None:
            raise ValueError(INCORRECT_SETUP_MSG)

        for handler in self.broker.handlers.values():  # pragma: no branch
            call = False
            batch = False

            if channel and (ch := handler.channel) is not None:
                call = bool(
                    (not ch.pattern and ch.name == channel)
                    or (
                        ch.pattern
                        and re.match(
                            ch.name.replace(".", "\\.").replace("*", ".*"),
                            channel,
                        )
                    )
                )

            if list and (ls := handler.list_sub) is not None:
                batch = ls.batch
                call = list == ls.name

            if stream and (st := handler.stream_sub) is not None:
                batch = st.batch
                call = stream == st.name

            if call:
                r = await call_handler(
                    handler=handler,
                    message=build_message(
                        message=[message] if batch else message,
                        channel=any_of,
                        headers=headers,
                        correlation_id=correlation_id,
                        reply_to=reply_to,
                    ),
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
        list: str,
    ) -> None:
        for handler in self.broker.handlers.values():  # pragma: no branch
            if handler.list_sub and handler.list_sub.name == list:
                await call_handler(
                    handler=handler,
                    message=build_message(
                        message=msgs,
                        channel=list,
                    ),
                )

        return None


def build_message(
    message: SendableMessage,
    channel: str,
    *,
    reply_to: str = "",
    correlation_id: Optional[str] = None,
    headers: Optional[AnyDict] = None,
) -> AnyRedisDict:
    data = RawMessage.encode(
        message=message,
        reply_to=reply_to,
        headers=headers,
        correlation_id=correlation_id,
    )
    return AnyRedisDict(
        channel=channel.encode(),
        data=data.encode(),
        type="message",
    )
