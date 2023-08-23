import asyncio
from itertools import chain
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    List,
    Optional,
    Sequence,
)

import anyio
from aiokafka import AIOKafkaConsumer, ConsumerRecord
from fast_depends.core import CallModel

from propan.__about__ import __version__
from propan._compat import Never, override
from propan.broker.handler import AsyncHandler
from propan.broker.message import PropanMessage
from propan.broker.parsers import resolve_custom_func
from propan.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    P_HandlerParams,
    T_HandlerReturn,
)
from propan.broker.wrapper import HandlerCallWrapper
from propan.kafka.parser import AioKafkaParser


class LogicHandler(AsyncHandler[ConsumerRecord]):
    topics: Sequence[str]
    group_id: Optional[str] = None

    consumer: Optional[AIOKafkaConsumer] = None
    task: Optional["asyncio.Task[Any]"] = None
    batch: bool = False

    @override
    def __init__(
        self,
        *topics: str,
        # Kafka information
        group_id: Optional[str] = None,
        client_id: str = "propan-" + __version__,
        builder: Callable[..., AIOKafkaConsumer],
        batch: bool = False,
        batch_timeout_ms: int = 200,
        max_records: Optional[int] = None,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        super().__init__(
            description=description,
            title=title,
        )

        self.group_id = group_id
        self.client_id = client_id
        self.topics = topics

        self.batch = batch
        self.batch_timeout_ms = batch_timeout_ms
        self.max_records = max_records

        self.builder = builder
        self.task = None
        self.consumer = None

    # TODO: use **kwargs: Unpack[ConsumerConnectionParams] with py3.12 release 2023-10-02
    async def start(self, **consumer_kwargs: Any) -> None:
        self.consumer = consumer = self.builder(
            *self.topics,
            group_id=self.group_id,
            client_id=self.client_id,
            **consumer_kwargs,
        )
        await consumer.start()
        self.task = asyncio.create_task(self._consume())

    async def close(self) -> None:
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
        handler: HandlerCallWrapper[ConsumerRecord, P_HandlerParams, T_HandlerReturn],
        dependant: CallModel[P_HandlerParams, T_HandlerReturn],
        parser: Optional[AsyncCustomParser[ConsumerRecord]],
        decoder: Optional[AsyncCustomDecoder[ConsumerRecord]],
        filter: Callable[[PropanMessage[ConsumerRecord]], Awaitable[bool]],
        middlewares: Optional[
            List[Callable[[PropanMessage[ConsumerRecord]], AsyncContextManager[None]]]
        ],
    ) -> None:
        parser_ = resolve_custom_func(
            parser,
            (
                AioKafkaParser.parse_message_batch
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
            decoder=decoder_,  # type: ignore[arg-type]
            filter=filter,
            dependant=dependant,
            middlewares=middlewares,
        )

    async def _consume(self) -> Never:
        assert self.consumer, "You need to start handler first"

        connected = True
        while True:
            try:
                if self.batch:
                    messages = await self.consumer.getmany(
                        timeout_ms=self.batch_timeout_ms,
                        max_records=self.max_records,
                    )
                    if not messages:
                        await anyio.sleep(self.batch_timeout_ms / 1000)
                        continue
                    msg = tuple(chain(*messages.values()))
                else:
                    msg = await self.consumer.getone()

            except Exception:
                if connected is True:
                    connected = False
                await anyio.sleep(5)

            else:
                if connected is False:
                    connected = True
                await self.consume(msg)
