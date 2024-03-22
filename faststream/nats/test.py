from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from uuid import uuid4

from nats.aio.msg import Msg
from typing_extensions import override

from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.parsers import encode_message
from faststream.broker.test import TestBroker, call_handler
from faststream.nats.broker import NatsBroker
from faststream.nats.handler import BaseNatsHandler
from faststream.nats.producer import NatsFastProducer
from faststream.nats.schemas.js_stream import is_subject_match_wildcard
from faststream.types import AnyDict, SendableMessage

if TYPE_CHECKING:
    from faststream.nats.asyncapi import Publisher

__all__ = ("TestNatsBroker",)


class TestNatsBroker(TestBroker[NatsBroker]):
    """A class to test NATS brokers."""

    @staticmethod
    def patch_publisher(broker: NatsBroker, publisher: Any) -> None:
        publisher._producer = broker._producer

    @staticmethod
    def create_publisher_fake_subscriber(
        broker: NatsBroker,
        publisher: "Publisher",
    ) -> HandlerCallWrapper[Any, Any, Any]:
        @broker.subscriber(publisher.subject)
        def f(msg: Any) -> None:
            pass

        return f

    @staticmethod
    async def _fake_connect(broker: NatsBroker, *args: Any, **kwargs: Any) -> None:
        broker._js_producer = broker._producer = FakeProducer(broker)  # type: ignore[assignment]

    @classmethod
    def _fake_start(cls, broker: NatsBroker, *args: Any, **kwargs: Any) -> None:
        super()._fake_start(broker, *args, **kwargs)

        for h in broker.handlers.values():
            h.producer = FakeProducer(broker)  # type: ignore[assignment]

    @staticmethod
    def remove_publisher_fake_subscriber(
        broker: NatsBroker, publisher: "Publisher"
    ) -> None:
        broker.handlers.pop(BaseNatsHandler.get_routing_hash(publisher.subject), None)


class FakeProducer(NatsFastProducer):
    def __init__(self, broker: NatsBroker) -> None:
        self.broker = broker

    @override
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
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
        incoming = build_message(
            message=message,
            subject=subject,
            headers=headers,
            correlation_id=correlation_id,
            reply_to=reply_to,
        )

        for handler in self.broker.handlers.values():  # pragma: no branch
            if stream and getattr(handler.stream, "name", None) != stream:
                continue

            if is_subject_match_wildcard(subject, handler.subject):
                if getattr(handler.pull_sub, "batch", False):
                    message = [incoming]
                else:
                    message = incoming

                r = await call_handler(
                    handler=handler,
                    message=message,
                    rpc=rpc,
                    rpc_timeout=rpc_timeout,
                    raise_timeout=raise_timeout,
                )

                if rpc:
                    return r

        return None


def build_message(
    message: SendableMessage,
    subject: str,
    *,
    reply_to: str = "",
    correlation_id: Optional[str] = None,
    headers: Optional[AnyDict] = None,
) -> "PatchedMessage":
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

