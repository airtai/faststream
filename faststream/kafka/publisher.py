from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union, cast

from aiokafka import ConsumerRecord
from typing_extensions import override

from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.kafka.producer import AioKafkaFastProducer
from faststream.types import AnyDict, SendableMessage

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware

@dataclass
class LogicPublisher(BasePublisher[ConsumerRecord]):
    """A class to publish messages to a Kafka topic.

    Attributes:
        _producer : An optional instance of AioKafkaFastProducer
        batch : A boolean indicating whether to send messages in batch
        client_id : A string representing the client ID

    Methods:
        publish : Publishes messages to the Kafka topic

    Raises:
        AssertionError: If `_producer` is not set up or if multiple messages are sent without the `batch` flag
    """

    topic: str
    partition: Optional[int]
    timestamp_ms: Optional[int]
    headers: Optional[Dict[str, str]]
    reply_to: Optional[str]
    client_id: str

    _producer: Optional[AioKafkaFastProducer]

    def __init__(
        self,
        *,
        topic: str,
        partition: Optional[int],
        timestamp_ms: Optional[int],
        headers: Optional[Dict[str, str]],
        reply_to: Optional[str],
        client_id: str,
        # Regular publisher options
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI options
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.topic = topic
        self.partition = partition
        self.timestamp_ms = timestamp_ms
        self.client_id = client_id
        self.reply_to = reply_to
        self.headers = headers

        self._producer = None

    @cached_property
    def publish_kwargs(self) -> AnyDict:
        return {
            "topic": self.topic,
            "partition": self.partition,
            "timestamp_ms": self.timestamp_ms,
            "headers": self.headers,
            "reply_to": self.reply_to,
        }


@dataclass
class DefaultPublisher(LogicPublisher):
    key: Optional[bytes]

    def __init__(
        self,
        *,
        key: Optional[bytes],
        topic: str,
        partition: Optional[int],
        timestamp_ms: Optional[int],
        headers: Optional[Dict[str, str]],
        reply_to: Optional[str],
        client_id: str,
        # Regular publisher options
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI options
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            topic=topic,
            partition=partition,
            timestamp_ms=timestamp_ms,
            client_id=client_id,
            reply_to=reply_to,
            headers=headers,
            # base publisher args
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.key = key

    @override
    async def _publish(  # type: ignore[override]
        self,
        message: SendableMessage = "",
        **kwargs: Any,
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101
        return await self._producer.publish(
            message=message,
            **kwargs,
        )

    @cached_property
    def publish_kwargs(self) -> AnyDict:
        return super().publish_kwargs | {"key": self.key}


class BatchPublisher(LogicPublisher):
    @override
    async def _publish(  # type: ignore[override]
        self,
        messages: Union[SendableMessage, Iterable[SendableMessage]],
        *extra_messages: SendableMessage,
        **kwargs: Any,
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        if extra_messages:
            msgs = (cast(SendableMessage, messages), *extra_messages)
        else:
            msgs = cast(Iterable[SendableMessage], messages)

        await self._producer.publish_batch(*msgs, **kwargs)
