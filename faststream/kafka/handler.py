import asyncio
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
)

import anyio
from aiokafka import AIOKafkaConsumer, ConsumerRecord
from aiokafka.errors import KafkaError
from typing_extensions import Unpack, override

from faststream.__about__ import __version__
from faststream.broker.core.handler import BaseHandler
from faststream.broker.core.publisher import FakePublisher
from faststream.broker.parsers import resolve_custom_func
from faststream.kafka.parser import AioKafkaParser
from faststream.kafka.shared.schemas import ConsumerConnectionParams
from faststream.types import AnyDict

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

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


class LogicHandler(BaseHandler[ConsumerRecord]):
    """A class to handle logic for consuming messages from Kafka.

    Attributes:
        topics : sequence of strings representing the topics to consume from
        group_id : optional string representing the consumer group ID
        consumer : optional AIOKafkaConsumer object representing the Kafka consumer
        task : optional asyncio.Task object representing the task for consuming messages
        batch : boolean indicating whether to consume messages in batches

    Methods:
        __init__ : constructor method for the LogicHandler class
        start : method to start consuming messages from Kafka
        close : method to close the Kafka consumer and cancel the consuming task
        add_call : method to add a handler call for processing consumed messages
        _consume : method to consume messages from Kafka and call the appropriate handler
    """

    topics: Sequence[str]
    group_id: Optional[str] = None

    consumer: Optional[AIOKafkaConsumer] = None
    task: Optional["asyncio.Task[Any]"] = None
    batch: bool = False

    @override
    def __init__(
        self,
        *topics: str,
        # Broker options
        watcher: Callable[..., AsyncContextManager[None]],
        extra_context: Optional[AnyDict] = None,
        graceful_timeout: Optional[float] = None,
        middlewares: Iterable["BrokerMiddleware[ConsumerRecord]"] = (),
        # Kafka information
        group_id: Optional[str] = None,
        client_id: str = "faststream-" + __version__,
        builder: Callable[..., AIOKafkaConsumer],
        is_manual: bool = False,
        batch: bool = False,
        batch_timeout_ms: int = 200,
        max_records: Optional[int] = None,
        # AsyncAPI information
        title_: Optional[str] = None,
        description_: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        """Initialize a Kafka consumer for the specified topics.

        Args:
            *topics: Variable length argument list of topics to consume from.
            log_context_builder: Callable that builds the log context.
            graceful_timeout: Optional timeout in seconds for graceful shutdown.
            group_id: Optional group ID for the consumer.
            client_id: Client ID for the consumer.
            builder: Callable that constructs an AIOKafkaConsumer instance.
            is_manual: Flag indicating whether to manually commit offsets.
            batch: Flag indicating whether to consume messages in batches.
            batch_timeout_ms: Timeout in milliseconds for batch consumption.
            max_records: Maximum number of records to consume in a batch.
            title: Optional title for the consumer.
            description: Optional description for the consumer.
            include_in_schema: Flag indicating whether to include the consumer in the API specification.

        Raises:
            NotImplementedError: If silent animals are not supported.

        """
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
        self.task = None
        self.consumer = None
        self.producer = None

    @override
    async def start(  # type: ignore[override]
        self,
        producer: Optional["PublisherProtocol"],
        **consumer_kwargs: Unpack[ConsumerConnectionParams],
    ) -> None:
        """Start the consumer.

        Args:
            **consumer_kwargs: Additional keyword arguments to pass to the consumer.
        """
        self.producer = producer

        self.consumer = consumer = self.builder(
            *self.topics,
            group_id=self.group_id,
            client_id=self.client_id,
            **consumer_kwargs,
        )
        await consumer.start()
        self.task = asyncio.create_task(self._consume())
        await super().start()

    async def close(self) -> None:
        await super().close()

        if self.consumer is not None:
            await self.consumer.stop()
            self.consumer = None

        if self.task is not None:
            self.task.cancel()
            self.task = None

    @override
    def add_call(  # type: ignore[override]
        self,
        *,
        filter: "Filter[StreamMessage[List[ConsumerRecord]]]",
        parser: Optional["CustomParser[List[ConsumerRecord]]"],
        decoder: Optional["CustomDecoder[StreamMessage[List[ConsumerRecord]]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[List[ConsumerRecord]]":
        """Adds a call to the handler.

        Args:
            handler: The handler function to be called.
            dependant: The dependant model.
            parser: Optional custom parser for parsing the input.
            decoder: Optional custom decoder for decoding the input.
            filter: The filter for filtering the input.
            middlewares: Optional sequence of middlewares to be applied.
        """
        parser_ = resolve_custom_func(  # type: ignore[type-var]
            parser,  # type: ignore[arg-type]
            (
                AioKafkaParser.parse_message_batch  # type: ignore[arg-type]
                if self.batch
                else AioKafkaParser.parse_message
            ),
        )
        decoder_ = resolve_custom_func(
            decoder,  # type: ignore[arg-type]
            (
                AioKafkaParser.decode_message_batch  # type: ignore[arg-type]
                if self.batch
                else AioKafkaParser.decode_message
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

                    msg = tuple(chain(*messages.values()))
                else:
                    msg = await self.consumer.getone()

            except KafkaError:  # pragma: no cover
                if connected is True:
                    connected = False
                await anyio.sleep(5)

            else:
                if connected is False:  # pragma: no cover
                    connected = True

                await self.consume(msg)

    @staticmethod
    def get_routing_hash(topics: Iterable[str], group_id: Optional[str] = None) -> str:
        return "".join((*topics, group_id or ""))

    @staticmethod
    def build_log_context(
        message: Optional["StreamMessage[ConsumerRecord]"],
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
        message: Optional["StreamMessage[ConsumerRecord]"],
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
