import asyncio
from itertools import chain
from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union

import anyio
from aiokafka import AIOKafkaConsumer, ConsumerRecord
from aiokafka.errors import KafkaError
from fast_depends.core import CallModel
from typing_extensions import Unpack, override

from faststream.__about__ import __version__
from faststream.broker.handler import AsyncHandler
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.parsers import resolve_custom_func
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.kafka.message import KafkaMessage
from faststream.kafka.parser import AioKafkaParser
from faststream.kafka.shared.schemas import ConsumerConnectionParams


class LogicHandler(AsyncHandler[ConsumerRecord]):
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
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        graceful_timeout: Optional[float] = None,
        # Kafka information
        group_id: Optional[str] = None,
        client_id: str = "faststream-" + __version__,
        builder: Callable[..., AIOKafkaConsumer],
        is_manual: bool = False,
        batch: bool = False,
        batch_timeout_ms: int = 200,
        max_records: Optional[int] = None,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
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
            log_context_builder=log_context_builder,
            description=description,
            title=title,
            include_in_schema=include_in_schema,
            graceful_timeout=graceful_timeout,
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

    @override
    async def start(  # type: ignore[override]
        self,
        **consumer_kwargs: Unpack[ConsumerConnectionParams],
    ) -> None:
        """Start the consumer.

        Args:
            **consumer_kwargs: Additional keyword arguments to pass to the consumer.

        Returns:
            None

        """
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

    def add_call(
        self,
        *,
        handler: HandlerCallWrapper[ConsumerRecord, P_HandlerParams, T_HandlerReturn],
        dependant: CallModel[P_HandlerParams, T_HandlerReturn],
        parser: CustomParser[
            Union[ConsumerRecord, Tuple[ConsumerRecord, ...]], KafkaMessage
        ],
        decoder: Optional[CustomDecoder[KafkaMessage]],
        filter: Union[
            Filter[KafkaMessage],
            Filter[StreamMessage[Tuple[ConsumerRecord, ...]]],
        ],
        middlewares: Optional[Sequence[Callable[[ConsumerRecord], BaseMiddleware]]],
    ) -> None:
        """Adds a call to the handler.

        Args:
            handler: The handler function to be called.
            dependant: The dependant model.
            parser: Optional custom parser for parsing the input.
            decoder: Optional custom decoder for decoding the input.
            filter: The filter for filtering the input.
            middlewares: Optional sequence of middlewares to be applied.

        Returns:
            None

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
        super().add_call(
            handler=handler,
            parser=parser_,
            decoder=decoder_,
            filter=filter,  # type: ignore[arg-type]
            dependant=dependant,
            middlewares=middlewares,
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
    def get_routing_hash(topics: Sequence[str], group_id: Optional[str] = None) -> str:
        return "".join((*topics, group_id or ""))
