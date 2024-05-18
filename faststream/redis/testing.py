import re
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union
from unittest.mock import AsyncMock, MagicMock

from typing_extensions import override

from faststream.broker.message import gen_cor_id
from faststream.exceptions import WRONG_PUBLISH_ARGS, SetupError
from faststream.redis.broker.broker import RedisBroker
from faststream.redis.message import (
    BatchListMessage,
    BatchStreamMessage,
    DefaultListMessage,
    DefaultStreamMessage,
    PubSubMessage,
    bDATA_KEY,
)
from faststream.redis.parser import RawMessage
from faststream.redis.publisher.producer import RedisFastProducer
from faststream.redis.schemas import INCORRECT_SETUP_MSG
from faststream.redis.subscriber.asyncapi import AsyncAPISubscriber
from faststream.testing.broker import TestBroker, call_handler

if TYPE_CHECKING:
    from faststream.broker.wrapper.call import HandlerCallWrapper
    from faststream.redis.publisher.asyncapi import AsyncAPIPublisher
    from faststream.types import AnyDict, SendableMessage

__all__ = ("TestRedisBroker",)


class TestRedisBroker(TestBroker[RedisBroker]):
    """A class to test Redis brokers."""

    @staticmethod
    def create_publisher_fake_subscriber(
        broker: RedisBroker,
        publisher: "AsyncAPIPublisher",
    ) -> "HandlerCallWrapper[Any, Any, Any]":
        sub = broker.subscriber(**publisher.subscriber_property)

        if not sub.calls:

            @sub
            def f(msg: Any) -> None:
                pass

            broker.setup_subscriber(sub)

        return sub.calls[0].handler

    @staticmethod
    async def _fake_connect(  # type: ignore[override]
        broker: RedisBroker,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncMock:
        broker._producer = FakeProducer(broker)  # type: ignore[assignment]
        connection = MagicMock()
        connection.pubsub.side_effect = AsyncMock
        return connection

    @staticmethod
    def remove_publisher_fake_subscriber(
        broker: RedisBroker,
        publisher: "AsyncAPIPublisher",
    ) -> None:
        broker._subscribers.pop(
            hash(AsyncAPISubscriber.create(**publisher.subscriber_property)),
            None,
        )


class FakeProducer(RedisFastProducer):
    def __init__(self, broker: RedisBroker) -> None:
        self.broker = broker

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "SendableMessage",
        *,
        channel: Optional[str] = None,
        list: Optional[str] = None,
        stream: Optional[str] = None,
        maxlen: Optional[int] = None,
        headers: Optional["AnyDict"] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> Optional[Any]:
        if rpc and reply_to:
            raise WRONG_PUBLISH_ARGS

        correlation_id = correlation_id or gen_cor_id()

        body = build_message(
            message=message,
            reply_to=reply_to,
            correlation_id=correlation_id,
            headers=headers,
        )

        any_of = channel or list or stream
        if any_of is None:
            raise SetupError(INCORRECT_SETUP_MSG)

        msg: Any = None
        for handler in self.broker._subscribers.values():  # pragma: no branch
            call = False

            if channel and (ch := getattr(handler, "channel", None)) is not None:
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

                msg = PubSubMessage(
                    type="message",
                    data=body,
                    channel=channel,
                    pattern=ch.pattern,
                )

            elif list and (ls := getattr(handler, "list_sub", None)) is not None:
                if ls.batch:
                    msg = BatchListMessage(
                        type="blist",
                        channel=list,
                        data=[body],
                    )

                else:
                    msg = DefaultListMessage(
                        type="list",
                        channel=list,
                        data=body,
                    )

                call = list == ls.name

            elif stream and (st := getattr(handler, "stream_sub", None)) is not None:
                if st.batch:
                    msg = BatchStreamMessage(
                        type="bstream",
                        channel=stream,
                        data=[{bDATA_KEY: body}],
                        message_ids=[],
                    )
                else:
                    msg = DefaultStreamMessage(
                        type="stream",
                        channel=stream,
                        data={bDATA_KEY: body},
                        message_ids=[],
                    )

                call = stream == st.name

            if call:
                r = await call_handler(
                    handler=handler,
                    message=msg,
                    rpc=rpc,
                    rpc_timeout=rpc_timeout,
                    raise_timeout=raise_timeout,
                )

                if rpc:  # pragma: no branch
                    return r

        return None

    async def publish_batch(
        self,
        *msgs: "SendableMessage",
        list: str,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        correlation_id = correlation_id or gen_cor_id()

        for handler in self.broker._subscribers.values():  # pragma: no branch
            if (
                list_sub := getattr(handler, "list_sub", None)
            ) and list_sub.name == list:
                await call_handler(
                    handler=handler,
                    message=BatchListMessage(
                        type="blist",
                        channel=list,
                        data=[
                            build_message(
                                m,
                                correlation_id=correlation_id,
                                headers=headers,
                            )
                            for m in msgs
                        ],
                    ),
                )

        return None


def build_message(
    message: Union[Sequence["SendableMessage"], "SendableMessage"],
    *,
    correlation_id: str,
    reply_to: str = "",
    headers: Optional["AnyDict"] = None,
) -> bytes:
    data = RawMessage.encode(
        message=message,
        reply_to=reply_to,
        headers=headers,
        correlation_id=correlation_id,
    )
    return data
