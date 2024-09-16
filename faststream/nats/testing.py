from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union
from unittest.mock import AsyncMock

import anyio
from nats.aio.msg import Msg
from typing_extensions import override

from faststream.broker.message import encode_message, gen_cor_id
from faststream.broker.utils import resolve_custom_func
from faststream.exceptions import WRONG_PUBLISH_ARGS, SubscriberNotFound
from faststream.nats.broker import NatsBroker
from faststream.nats.parser import NatsParser
from faststream.nats.publisher.producer import NatsFastProducer
from faststream.nats.schemas.js_stream import is_subject_match_wildcard
from faststream.testing.broker import TestBroker
from faststream.utils.functions import timeout_scope

if TYPE_CHECKING:
    from faststream.nats.publisher.asyncapi import AsyncAPIPublisher
    from faststream.nats.subscriber.usecase import LogicSubscriber
    from faststream.types import SendableMessage

__all__ = ("TestNatsBroker",)


class TestNatsBroker(TestBroker[NatsBroker]):
    """A class to test NATS brokers."""

    @staticmethod
    def create_publisher_fake_subscriber(
        broker: NatsBroker,
        publisher: "AsyncAPIPublisher",
    ) -> Tuple["LogicSubscriber[Any, Any]", bool]:
        sub: Optional[LogicSubscriber[Any, Any]] = None
        publisher_stream = publisher.stream.name if publisher.stream else None
        for handler in broker._subscribers.values():
            if _is_handler_suitable(handler, publisher.subject, publisher_stream):
                sub = handler
                break

        if sub is None:
            is_real = False
            sub = broker.subscriber(publisher.subject)
        else:
            is_real = True

        return sub, is_real

    @staticmethod
    async def _fake_connect(  # type: ignore[override]
        broker: NatsBroker,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncMock:
        broker.stream = AsyncMock()
        broker._js_producer = broker._producer = FakeProducer(  # type: ignore[assignment]
            broker,
        )
        return AsyncMock()


class FakeProducer(NatsFastProducer):
    def __init__(self, broker: NatsBroker) -> None:
        self.broker = broker

        default = NatsParser(pattern="", no_ack=False)
        self._parser = resolve_custom_func(broker._parser, default.parse_message)
        self._decoder = resolve_custom_func(broker._decoder, default.decode_message)

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
            if _is_handler_suitable(handler, subject, stream):
                msg: Union[List[PatchedMessage], PatchedMessage]

                if (pull := getattr(handler, "pull_sub", None)) and pull.batch:
                    msg = [incoming]
                else:
                    msg = incoming

                with timeout_scope(rpc_timeout, raise_timeout):
                    response = await self._execute_handler(msg, subject, handler)
                    if rpc:
                        return await self._decoder(await self._parser(response))

        return None

    @override
    async def request(  # type: ignore[override]
        self,
        message: "SendableMessage",
        subject: str,
        *,
        correlation_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 0.5,
        # NatsJSFastProducer compatibility
        stream: Optional[str] = None,
    ) -> "PatchedMessage":
        incoming = build_message(
            message=message,
            subject=subject,
            headers=headers,
            correlation_id=correlation_id,
        )

        for handler in self.broker._subscribers.values():  # pragma: no branch
            if _is_handler_suitable(handler, subject, stream):
                msg: Union[List[PatchedMessage], PatchedMessage]

                if (pull := getattr(handler, "pull_sub", None)) and pull.batch:
                    msg = [incoming]
                else:
                    msg = incoming

                with anyio.fail_after(timeout):
                    return await self._execute_handler(msg, subject, handler)

        raise SubscriberNotFound

    async def _execute_handler(
        self,
        msg: Any,
        subject: str,
        handler: "LogicSubscriber[Any, Any]",
    ) -> "PatchedMessage":
        result = await handler.process_message(msg)

        return build_message(
            subject=subject,
            message=result.body,
            headers=result.headers,
            correlation_id=result.correlation_id,
        )


def _is_handler_suitable(
    handler: "LogicSubscriber[Any, Any]",
    subject: str,
    stream: Optional[str] = None,
) -> bool:
    if stream:
        if not (handler_stream := getattr(handler, "stream", None)):
            return False

        if stream != handler_stream.name:
            return False

    if is_subject_match_wildcard(subject, handler.clear_subject):
        return True

    for filter_subject in handler.config.filter_subjects or ():
        if is_subject_match_wildcard(subject, filter_subject):
            return True

    return False


def build_message(
    message: "SendableMessage",
    subject: str,
    *,
    reply_to: str = "",
    correlation_id: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
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
        self,
        timeout: float = 1,
    ) -> "PatchedMessage":  # pragma: no cover
        return self

    async def nak(self, delay: Union[int, float, None] = None) -> None:
        pass

    async def term(self) -> None:
        pass

    async def in_progress(self) -> None:
        pass
