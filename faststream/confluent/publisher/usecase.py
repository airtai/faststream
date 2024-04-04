from contextlib import AsyncExitStack
from itertools import chain
from typing import Any, Dict, Iterable, Optional, Union, cast

from confluent_kafka import Message
from typing_extensions import override

from faststream.broker.publisher.usecase import PublisherUsecase
from faststream.broker.types import BrokerMiddleware, PublisherMiddleware
from faststream.confluent.publisher.producer import AsyncConfluentFastProducer
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.types import AnyDict, SendableMessage


class LogicPublisher(PublisherUsecase[Message]):
    """A class to publish messages to a Kafka topic."""

    _producer: Optional[AsyncConfluentFastProducer]

    def __init__(
        self,
        *,
        topic: str,
        partition: Optional[int],
        timestamp_ms: Optional[int],
        headers: Optional[Dict[str, str]],
        reply_to: Optional[str],
        # Publisher args
        broker_middlewares: Iterable[BrokerMiddleware[Message]],
        middlewares: Iterable[PublisherMiddleware],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.topic = topic
        self.partition = partition
        self.timestamp_ms = timestamp_ms
        self.reply_to = reply_to
        self.headers = headers

        self._producer = None

    def __hash__(self) -> int:
        return hash(self.topic)

    def add_prefix(self, prefix: str) -> None:
        self.topic = "".join((prefix, self.topic))


class DefaultPublisher(LogicPublisher):
    def __init__(
        self,
        *,
        key: Optional[bytes],
        topic: str,
        partition: Optional[int],
        timestamp_ms: Optional[int],
        headers: Optional[Dict[str, str]],
        reply_to: Optional[str],
        # Publisher args
        broker_middlewares: Iterable[BrokerMiddleware[Message]],
        middlewares: Iterable[PublisherMiddleware],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            topic=topic,
            partition=partition,
            timestamp_ms=timestamp_ms,
            reply_to=reply_to,
            headers=headers,
            # publisher args
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.key = key

    @override
    async def publish(
        self,
        message: SendableMessage,
        topic: str = "",
        *,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        reply_to: str = "",
        # publisher specific
        extra_middlewares: Iterable[PublisherMiddleware] = (),
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs: "AnyDict" = {
            "key": key or self.key,
            # basic args
            "topic": topic or self.topic,
            "partition": partition or self.partition,
            "timestamp_ms": timestamp_ms or self.timestamp_ms,
            "headers": headers or self.headers,
            "reply_to": reply_to or self.reply_to,
            "correlation_id": correlation_id,
        }

        async with AsyncExitStack() as stack:
            for m in chain(
                extra_middlewares
                or (m(None).publish_scope for m in self._broker_middlewares),
                self._middlewares,
            ):
                message = await stack.enter_async_context(
                    m(message, **kwargs)
                )

            return await self._producer.publish(message=message, **kwargs)

        return None


class BatchPublisher(LogicPublisher):
    @override
    async def publish(  # type: ignore[override]
        self,
        message: Union[SendableMessage, Iterable[SendableMessage]],
        *extra_messages: SendableMessage,
        topic: str = "",
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
        # publisher specific
        extra_middlewares: Iterable[PublisherMiddleware] = (),
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        msgs: Iterable[SendableMessage]
        if extra_messages:
            msgs = (cast(SendableMessage, message), *extra_messages)
        else:
            msgs = cast(Iterable[SendableMessage], message)

        kwargs: "AnyDict" = {
            "topic": topic or self.topic,
            "partition": partition or self.partition,
            "timestamp_ms": timestamp_ms or self.timestamp_ms,
            "headers": headers or self.headers,
            "reply_to": reply_to or self.reply_to,
            "correlation_id": correlation_id,
        }

        async with AsyncExitStack() as stack:
            wrapped_messages = [
                await stack.enter_async_context(
                    middleware(msg, **kwargs)
                )
                for msg in msgs
                for middleware in chain(
                    extra_middlewares
                    or (m(None).publish_scope for m in self._broker_middlewares),
                    self._middlewares,
                )
            ] or msgs

            return await self._producer.publish_batch(*wrapped_messages, **kwargs)

        return None
