import asyncio
from itertools import chain
from typing import (TYPE_CHECKING, Any, Dict, Callable, Iterable, Optional, Sequence, Tuple, Union, AsyncContextManager, )
import anyio
from confluent_kafka import KafkaException, Message
from typing_extensions import Unpack, override

from faststream.__about__ import SERVICE_NAME
from faststream.broker.core.handler import BaseHandler
from faststream.broker.core.publisher import FakePublisher
from faststream.broker.parsers import resolve_custom_func
from faststream.confluent.client import AsyncConfluentConsumer
from faststream.confluent.parser import AsyncConfluentParser
from faststream.confluent.shared.schemas import ConsumerConnectionParams

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends
    from faststream.types import AnyDict

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherProtocol,
        SubscriberMiddleware,
    )


class LogicHandler(BaseHandler[Message]):
    """A class to handle logic for consuming messages from Kafka."""

    topics: Sequence[str]
    group_id: Optional[str]

    consumer: Optional[AsyncConfluentConsumer]
    task: Optional["asyncio.Task[Any]"]
    batch: bool

    @override
    def __init__(
        self,
        *topics: str,
        # Broker options
        watcher: Callable[..., AsyncContextManager[None]],
        extra_context: Optional["AnyDict"] = None,
        graceful_timeout: Optional[float] = None,
        middlewares: Iterable["BrokerMiddleware[Message]"] = (),
        # Kafka information
        group_id: Optional[str] = None,
        client_id: str = SERVICE_NAME,
        builder: Callable[..., AsyncConfluentConsumer],
        is_manual: bool = False,
        batch: bool = False,
        batch_timeout_ms: int = 200,
        max_records: Optional[int] = None,
        # AsyncAPI information
        title_: Optional[str] = None,
        description_: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        """Initialize a Kafka consumer for the specified topics."""
        super().__init__(
            middlewares=middlewares,
            graceful_timeout=graceful_timeout,
            watcher=watcher,
            extra_context=extra_context,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.group_id = group_id
        self.client_id = client_id
        self.topics = topics

        self.batch = batch
        self.batch_timeout_ms = batch_timeout_ms
        self.max_records = max_records
        self.is_manual = is_manual

        self.builder = builder
        self.consumer = None
        self.producer = None
        self.task = None

    @override
    async def start(  # type: ignore[override]
        self,
        producer: Optional["PublisherProtocol"],
        **consumer_kwargs: Unpack[ConsumerConnectionParams],
    ) -> None:
        """Start the consumer."""
        self.consumer = consumer = self.builder(
            *self.topics,
            group_id=self.group_id,
            client_id=self.client_id,
            **consumer_kwargs,
        )
        await consumer.start()

        await super().start(producer=producer)
        self.task = asyncio.create_task(self._consume())

    async def close(self) -> None:
        await super().close()

        if self.consumer is not None:
            await self.consumer.stop()
            self.consumer = None

        if self.task is not None and not self.task.done():
            self.task.cancel()

        self.task = None

    @override
    def add_call(  # type: ignore[override]
        self,
        *,
        filter: "Filter[StreamMessage[Message]]",
        parser: Optional["CustomParser[Message]"],
        decoder: Optional["CustomDecoder[StreamMessage[Message]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[Message]":
        """Adds a call to the handler."""
        parser_ = resolve_custom_func(  # type: ignore[type-var]
            parser,  # type: ignore[arg-type]
            (
                AsyncConfluentParser.parse_message_batch  # type: ignore[arg-type]
                if self.batch
                else AsyncConfluentParser.parse_message
            ),
        )
        decoder_ = resolve_custom_func(
            decoder,  # type: ignore[arg-type]
            (
                AsyncConfluentParser.decode_message_batch  # type: ignore[arg-type]
                if self.batch
                else AsyncConfluentParser.decode_message
            ),
        )
        return super().add_call(
            parser_=parser_,
            decoder_=decoder_,
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    def make_response_publisher(
        self, message: "StreamMessage[Any]"
    ) -> Sequence[FakePublisher]:
        if not message.reply_to or self.producer is None:
            return ()

        return (
            FakePublisher(
                self.producer.publish,
                topic=message.reply_to,
            ),
        )

    async def _consume(self) -> None:
        assert self.consumer, "You need to start handler first"  # nosec B101

        connected = True
        while self.running:
            try:
                if self.batch:
                    messages = await self.consumer.getmany(
                        timeout_ms=self.batch_timeout_ms,
                        max_records=self.max_records,
                    )

                    if not messages:  # pragma: no cover
                        await anyio.sleep(self.batch_timeout_ms / 1000)
                        continue

                    msg: Union[Message, Tuple[Message, ...]] = tuple(
                        chain(*messages.values())
                    )
                else:
                    msg = await self.consumer.getone()

            except KafkaException:  # pragma: no cover
                if connected is True:
                    connected = False
                await anyio.sleep(5)

            else:
                if connected is False:  # pragma: no cover
                    connected = True

                await self.consume(msg)  # type: ignore[arg-type]

    @staticmethod
    def get_routing_hash(topics: Sequence[str], group_id: Optional[str] = None) -> str:
        return "".join((*topics, group_id or ""))

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

    def get_log_context(
        self,
        message: Optional["StreamMessage[Message]"],
    ) -> Dict[str, str]:
        if message is None:
            topic = ",".join(self.topics)
        elif isinstance(message.raw_message, Sequence):
            topic = message.raw_message[0].topic
        else:
            topic = message.raw_message.topic

        return self.build_log_context(
            message=message,
            topic=topic,
            group_id=self.group_id,
        )