import asyncio
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Sequence,
    Tuple,
)

import anyio
from confluent_kafka import KafkaException, Message
from typing_extensions import override

from faststream.broker.publisher.fake import FakePublisher
from faststream.broker.subscriber.usecase import SubscriberUsecase
from faststream.broker.types import MsgType
from faststream.confluent.parser import AsyncConfluentParser

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream.broker.message import StreamMessage
    from faststream.broker.publisher.proto import ProducerProto
    from faststream.broker.types import (
        AsyncCallable,
        BrokerMiddleware,
        CustomCallable,
    )
    from faststream.confluent.client import AsyncConfluentConsumer
    from faststream.types import AnyDict, Decorator, LoggerProto


class LogicSubscriber(ABC, SubscriberUsecase[MsgType]):
    """A class to handle logic for consuming messages from Kafka."""

    topics: Sequence[str]
    group_id: Optional[str]

    builder: Optional[Callable[..., "AsyncConfluentConsumer"]]
    consumer: Optional["AsyncConfluentConsumer"]

    task: Optional["asyncio.Task[None]"]
    client_id: Optional[str]

    def __init__(
        self,
        *topics: str,
        # Kafka information
        group_id: Optional[str],
        connection_data: "AnyDict",
        is_manual: bool,
        # Subscriber args
        default_parser: "AsyncCallable",
        default_decoder: "AsyncCallable",
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[MsgType]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            default_parser=default_parser,
            default_decoder=default_decoder,
            # Propagated args
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.group_id = group_id
        self.topics = topics
        self.is_manual = is_manual
        self.builder = None
        self.consumer = None
        self.task = None

        # Setup it later
        self.client_id = ""
        self.__connection_data = connection_data

    @override
    def setup(  # type: ignore[override]
        self,
        *,
        client_id: Optional[str],
        builder: Callable[..., "AsyncConfluentConsumer"],
        # basic args
        logger: Optional["LoggerProto"],
        producer: Optional["ProducerProto"],
        graceful_timeout: Optional[float],
        extra_context: "AnyDict",
        # broker options
        broker_parser: Optional["CustomCallable"],
        broker_decoder: Optional["CustomCallable"],
        # dependant args
        apply_types: bool,
        is_validate: bool,
        _get_dependant: Optional[Callable[..., Any]],
        _call_decorators: Iterable["Decorator"],
    ) -> None:
        self.client_id = client_id
        self.builder = builder

        super().setup(
            logger=logger,
            producer=producer,
            graceful_timeout=graceful_timeout,
            extra_context=extra_context,
            broker_parser=broker_parser,
            broker_decoder=broker_decoder,
            apply_types=apply_types,
            is_validate=is_validate,
            _get_dependant=_get_dependant,
            _call_decorators=_call_decorators,
        )

    @override
    async def start(self) -> None:
        """Start the consumer."""
        assert self.builder, "You should setup subscriber at first."  # nosec B101

        self.consumer = consumer = self.builder(
            *self.topics,
            group_id=self.group_id,
            client_id=self.client_id,
            **self.__connection_data,
        )
        await consumer.start()

        await super().start()

        self.task = asyncio.create_task(self._consume())

    async def close(self) -> None:
        await super().close()

        if self.consumer is not None:
            await self.consumer.stop()
            self.consumer = None

        if self.task is not None and not self.task.done():
            self.task.cancel()

        self.task = None

    def _make_response_publisher(
        self, message: "StreamMessage[Any]"
    ) -> Sequence[FakePublisher]:
        if not message.reply_to or self._producer is None:
            return ()

        return (
            FakePublisher(
                self._producer.publish,
                publish_kwargs={
                    "topic": message.reply_to,
                },
            ),
        )

    @abstractmethod
    async def get_msg(self) -> Optional[MsgType]:
        raise NotImplementedError()

    async def _consume(self) -> None:
        assert self.consumer, "You should start subscriber at first."  # nosec B101

        connected = True
        while self.running:
            try:
                msg = await self.get_msg()
            except KafkaException:  # pragma: no cover  # noqa: PERF203
                if connected:
                    connected = False
                await anyio.sleep(5)

            else:
                if not connected:  # pragma: no cover
                    connected = True

                if msg is not None:
                    await self.consume(msg)  # type: ignore[arg-type]

    @staticmethod
    def get_routing_hash(topics: Iterable[str], group_id: Optional[str] = None) -> int:
        return hash("".join((*topics, group_id or "")))

    def __hash__(self) -> int:
        return self.get_routing_hash(self.topics, self.group_id)

    @staticmethod
    def build_log_context(
        message: Optional["StreamMessage[Any]"],
        topic: str,
        group_id: Optional[str] = None,
    ) -> Dict[str, str]:
        return {
            "topic": topic,
            "group_id": group_id or "",
            "message_id": getattr(message, "message_id", ""),
        }

    def add_prefix(self, prefix: str) -> None:
        self.topics = tuple("".join((prefix, t)) for t in self.topics)


class DefaultSubscriber(LogicSubscriber[Message]):
    def __init__(
        self,
        *topics: str,
        # Kafka information
        group_id: Optional[str],
        connection_data: "AnyDict",
        is_manual: bool,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[Message]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            *topics,
            group_id=group_id,
            connection_data=connection_data,
            is_manual=is_manual,
            # subscriber args
            default_parser=AsyncConfluentParser.parse_message,
            default_decoder=AsyncConfluentParser.decode_message,
            # Propagated args
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    async def get_msg(self) -> Optional["Message"]:
        assert self.consumer, "You should setup subscriber at first."  # nosec B101
        return await self.consumer.getone()

    def get_log_context(
        self,
        message: Optional["StreamMessage[Message]"],
    ) -> Dict[str, str]:
        if message is None:
            topic = ",".join(self.topics)
        else:
            topic = message.raw_message.topic() or ",".join(self.topics)

        return self.build_log_context(
            message=message,
            topic=topic,
            group_id=self.group_id,
        )


class BatchSubscriber(LogicSubscriber[Tuple[Message, ...]]):
    def __init__(
        self,
        *topics: str,
        batch_timeout_ms: int,
        max_records: Optional[int],
        # Kafka information
        group_id: Optional[str],
        connection_data: "AnyDict",
        is_manual: bool,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[Tuple[Message, ...]]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        self.batch_timeout_ms = batch_timeout_ms
        self.max_records = max_records

        super().__init__(
            *topics,
            group_id=group_id,
            connection_data=connection_data,
            is_manual=is_manual,
            # subscriber args
            default_parser=AsyncConfluentParser.parse_message_batch,
            default_decoder=AsyncConfluentParser.decode_message_batch,
            # Propagated args
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    async def get_msg(self) -> Optional[Tuple["Message", ...]]:
        assert self.consumer, "You should setup subscriber at first."  # nosec B101

        messages = await self.consumer.getmany(
            timeout_ms=self.batch_timeout_ms,
            max_records=self.max_records,
        )

        if not messages:  # pragma: no cover
            await anyio.sleep(self.batch_timeout_ms / 1000)
            return None

        return messages

    def get_log_context(
        self,
        message: Optional["StreamMessage[Tuple[Message, ...]]"],
    ) -> Dict[str, str]:
        if message is None:
            topic = ",".join(self.topics)
        else:
            topic = message.raw_message[0].topic() or ",".join(self.topics)

        return self.build_log_context(
            message=message,
            topic=topic,
            group_id=self.group_id,
        )
