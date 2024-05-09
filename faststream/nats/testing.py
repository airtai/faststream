from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock

from nats.aio.msg import Msg
from typing_extensions import override

from faststream.broker.message import encode_message, gen_cor_id
from faststream.exceptions import WRONG_PUBLISH_ARGS
from faststream.nats.broker import NatsBroker
from faststream.nats.publisher.producer import NatsFastProducer
from faststream.nats.schemas.js_stream import is_subject_match_wildcard
from faststream.nats.subscriber.asyncapi import AsyncAPISubscriber
from faststream.testing.broker import TestBroker, call_handler

if TYPE_CHECKING:
    from faststream.broker.wrapper.call import HandlerCallWrapper
    from faststream.nats.publisher.asyncapi import AsyncAPIPublisher
    from faststream.types import AnyDict, SendableMessage

__all__ = ("TestNatsBroker",)


class TestNatsBroker(TestBroker[NatsBroker]):
    """A class to test NATS brokers."""

    @staticmethod
    def create_publisher_fake_subscriber(
        broker: NatsBroker,
        publisher: "AsyncAPIPublisher",
    ) -> "HandlerCallWrapper[Any, Any, Any]":
        sub = broker.subscriber(publisher.subject)

        if not sub.calls:

            @sub
            def f(msg: Any) -> None:
                pass

            broker.setup_subscriber(sub)

        return sub.calls[0].handler

    @staticmethod
    async def _fake_connect(  # type: ignore[override]
        broker: NatsBroker,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncMock:
        broker.stream = AsyncMock()  # type: ignore[assignment]
        broker._js_producer = broker._producer = FakeProducer(broker)  # type: ignore[assignment]
        return AsyncMock()

    @staticmethod
    def remove_publisher_fake_subscriber(
        broker: NatsBroker, publisher: "AsyncAPIPublisher"
    ) -> None:
        broker._subscribers.pop(
            AsyncAPISubscriber.get_routing_hash(publisher.subject), None
        )


class FakeProducer(NatsFastProducer):
    def __init__(self, broker: NatsBroker) -> None:
        self.broker = broker

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "SendableMessage",
        subject: str,
        reply_to: str = "",
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        # NatsJSFastProducer compatibility
        timeout: Optional[float] = None,
        stream: Optional[str] = None,
        *,
        rpc: bool = False,
        rpc_timeout: Optional[float] = None,
        raise_timeout: bool = False,
    ) -> Any:
        if rpc and reply_to:
            raise WRONG_PUBLISH_ARGS

        incoming = build_message(
            message=message,
            subject=subject,
            headers=headers,
            correlation_id=correlation_id,
            reply_to=reply_to,
        )

        for handler in self.broker._subscribers.values():  # pragma: no branch
            if stream and getattr(handler.stream, "name", None) != stream:
                continue

            if is_subject_match_wildcard(subject, handler.subject):
                msg: Union[List[PatchedMessage], PatchedMessage]
                if getattr(handler.pull_sub, "batch", False):
                    msg = [incoming]
                else:
                    msg = incoming

                r = await call_handler(
                    handler=handler,
                    message=msg,
                    rpc=rpc,
                    rpc_timeout=rpc_timeout,
                    raise_timeout=raise_timeout,
                )

                if rpc:
                    return r

        return None


def build_message(
    message: "SendableMessage",
    subject: str,
    *,
    reply_to: str = "",
    correlation_id: Optional[str] = None,
    headers: Optional["AnyDict"] = None,
) -> "PatchedMessage":
    msg, content_type = encode_message(message)
    return PatchedMessage(
        _client=None,  # type: ignore
        subject=subject,
        reply=reply_to,
        data=msg,
        headers={
            "content-type": content_type or "",
            "correlation_id": correlation_id or gen_cor_id(),
            **(headers or {}),
        },
    )


class PatchedMessage(Msg):
    async def ack(self) -> None:
        pass

    async def ack_sync(
        self, timeout: float = 1
    ) -> "PatchedMessage":  # pragma: no cover
        return self

    async def nak(self, delay: Union[int, float, None] = None) -> None:
        pass

    async def term(self) -> None:
        pass

    async def in_progress(self) -> None:
        pass
