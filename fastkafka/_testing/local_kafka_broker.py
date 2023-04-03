# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/001_LocalKafkaBroker.ipynb.

# %% auto 0
__all__ = ['logger', 'create_consumer_record', 'ConsumerMetadata', 'LocalKafkaBroker']

# %% ../../nbs/001_LocalKafkaBroker.ipynb 1
import uuid
from collections import namedtuple
from dataclasses import dataclass

from typing import *
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.structs import ConsumerRecord, TopicPartition

from .._components.meta import patch, delegates
from .._components.logger import get_logger

# %% ../../nbs/001_LocalKafkaBroker.ipynb 3
logger = get_logger(__name__)

# %% ../../nbs/001_LocalKafkaBroker.ipynb 5
def create_consumer_record(topic: str, msg: bytes):
    record = ConsumerRecord(
        topic=topic,
        partition=0,
        offset=0,
        timestamp=0,
        timestamp_type=0,
        key=None,
        value=msg,
        checksum=0,
        serialized_key_size=0,
        serialized_value_size=0,
        headers=[],
    )
    return record

# %% ../../nbs/001_LocalKafkaBroker.ipynb 7
@dataclass
class ConsumerMetadata:
    topic: str
    offset: int

# %% ../../nbs/001_LocalKafkaBroker.ipynb 9
class LocalKafkaBroker:
    def __init__(self, topics: List[str]):
        self.data: Dict[str, List[ConsumerRecord]] = {topic: list() for topic in topics}

        self.consumers_metadata: Dict[str, List[ConsumerMetadata]] = {}

    def connect(self) -> str:
        return uuid.uuid4()

    def subscribe(self, actor_id: str, *, auto_offest_reset: str, topic: str) -> None:
        consumer_metadata = self.consumers_metadata.get(actor_id, list())
        consumer_metadata.append(
            ConsumerMetadata(
                topic, len(self.data[topic]) if auto_offest_reset == "latest" else 0
            )
        )
        self.consumers_metadata[actor_id] = consumer_metadata

    def unsubscribe(self, actor_id: str):
        try:
            del self.consumers_metadata[actor_id]
        except KeyError:
            logger.warning(f"No subscription with {actor_id=} found!")

    def produce(
        self, actor_id: str, *, topic: str, msg: bytes, key: Optional[bytes]
    ) -> None:
        record = create_consumer_record(topic, msg)
        self.data[topic].append(record)

    def consume(
        self, actor_id: str
    ) -> Dict[TopicPartition, List[ConsumerRecord]]:  # topic to list of messages
        msgs = {}

        try:
            consumer_metadata = self.consumers_metadata[actor_id]
        except KeyError:
            logger.warn(f"No subscription with {actor_id=} found!")
            return msgs

        for metadata in consumer_metadata:
            try:
                msgs[TopicPartition(metadata.topic, 0)] = self.data[metadata.topic][
                    metadata.offset :
                ]
                metadata.offset = len(self.data[metadata.topic])
            except KeyError:
                raise RuntimeError(
                    f"{metadata.topic=} not found, did you pass it to LocalKafkaBroker on init to be created?"
                )
        return msgs

    def _patch_consumers_and_producers(self) -> None:
        pass

    def __enter__(self) -> AsyncGenerator["LocalKafkaBroker", None]:
        logger.info("Local kafka broker starting")
        self._patch_consumers_and_producers()
        return self

    def __exit__(self, *args: Any) -> None:
        logger.info("Local kafka broker stopping")

# %% ../../nbs/001_LocalKafkaBroker.ipynb 19
def _patch_AIOKafkaConsumer_init(broker: LocalKafkaBroker) -> None:
    @patch
    @delegates(AIOKafkaConsumer)
    def __init__(
        self: AIOKafkaConsumer,
        broker: LocalKafkaBroker = broker,
        auto_offset_reset="latest",  # check if latest or earliest
        **kwargs: Any
    ) -> None:
        logger.info("AIOKafkaConsumer patched __init__() called()")
        self.broker = broker
        self.auto_offset_reset = auto_offset_reset
        self.id: Optional[str] = None

# %% ../../nbs/001_LocalKafkaBroker.ipynb 22
def _patch_AIOKafkaConsumer_start() -> None:
    @patch
    @delegates(AIOKafkaConsumer.start)
    async def start(self: AIOKafkaConsumer, **kwargs: Any) -> None:
        logger.info("AIOKafkaConsumer patched start() called()")
        if self.id is not None:
            raise RuntimeError(
                "Consumer start() already called! Run consumer stop() before running start() again"
            )
        self.id = self.broker.connect()

# %% ../../nbs/001_LocalKafkaBroker.ipynb 25
def _patch_AIOKafkaConsumer_subscribe() -> None:
    @patch
    @delegates(AIOKafkaConsumer.subscribe)
    def subscribe(self: AIOKafkaConsumer, topics: List[str], **kwargs: Any) -> None:
        logger.info("AIOKafkaConsumer patched subscribe() called")
        if self.id is None:
            raise RuntimeError(
                "Consumer start() not called! Run consumer start() first"
            )
        logger.info(f"AIOKafkaConsumer.subscribe(), subscribing to: {topics}")
        [
            self.broker.subscribe(
                self.id, topic=topic, auto_offest_reset=self.auto_offset_reset
            )
            for topic in topics
        ]

# %% ../../nbs/001_LocalKafkaBroker.ipynb 28
def _patch_AIOKafkaConsumer_stop() -> None:
    @patch
    @delegates(AIOKafkaConsumer.stop)
    async def stop(self: AIOKafkaConsumer, **kwargs: Any) -> None:
        logger.info("AIOKafkaConsumer patched stop() called")
        if self.id is None:
            raise RuntimeError(
                "Consumer start() not called! Run consumer start() first"
            )
        self.broker.unsubscribe(self.id)

# %% ../../nbs/001_LocalKafkaBroker.ipynb 31
def _patch_AIOKafkaConsumer_getmany() -> None:
    @patch
    @delegates(AIOKafkaConsumer.getmany)
    async def getmany(
        self: AIOKafkaConsumer, **kwargs: Any
    ) -> Dict[TopicPartition, List[ConsumerRecord]]:
        logger.info("AIOKafkaConsumer patched getmany() called!")
        return self.broker.consume(self.id)

# %% ../../nbs/001_LocalKafkaBroker.ipynb 34
def _patch_AIOKafkaConsumer(broker: LocalKafkaBroker) -> None:
    _patch_AIOKafkaConsumer_init(broker)
    _patch_AIOKafkaConsumer_start()
    _patch_AIOKafkaConsumer_subscribe()
    _patch_AIOKafkaConsumer_stop()
    _patch_AIOKafkaConsumer_getmany()

# %% ../../nbs/001_LocalKafkaBroker.ipynb 38
def _patch_AIOKafkaProducer_init(broker: LocalKafkaBroker) -> None:
    @patch
    @delegates(AIOKafkaProducer)
    def __init__(
        self: AIOKafkaProducer, broker: LocalKafkaBroker = broker, **kwargs: Any
    ) -> None:
        logger.info("AIOKafkaProducer patched __init__() called()")
        self.broker = broker
        self.id: Optional[str] = None

# %% ../../nbs/001_LocalKafkaBroker.ipynb 41
def _patch_AIOKafkaProducer_start() -> None:
    @patch
    @delegates(AIOKafkaProducer.start)
    async def start(self: AIOKafkaProducer, **kwargs: Any) -> None:
        logger.info("AIOKafkaProducer patched start() called()")
        if self.id is not None:
            raise RuntimeError(
                "Producer start() already called! Run producer stop() before running start() again"
            )
        self.id = self.broker.connect()

# %% ../../nbs/001_LocalKafkaBroker.ipynb 44
def _patch_AIOKafkaProducer_stop() -> None:
    @patch
    @delegates(AIOKafkaProducer.stop)
    async def stop(self: AIOKafkaProducer, **kwargs: Any) -> None:
        logger.info("AIOKafkaProducer patched stop() called")
        if self.id is None:
            raise RuntimeError(
                "Producer start() not called! Run producer start() first"
            )

# %% ../../nbs/001_LocalKafkaBroker.ipynb 47
def _patch_AIOKafkaProducer_send() -> None:
    @patch
    @delegates(AIOKafkaProducer.send)
    async def send(
        self: AIOKafkaProducer,
        topic: str,
        msg: bytes,
        key: Optional[bytes] = None,
        **kwargs: Any
    ) -> None:
        # logger.info("AIOKafkaProducer patched send() called()")
        if self.id is None:
            raise RuntimeError(
                "Producer start() not called! Run producer start() first"
            )
        self.broker.produce(self.id, topic=topic, msg=msg, key=key)

# %% ../../nbs/001_LocalKafkaBroker.ipynb 50
def _patch_AIOKafkaProducer(broker: LocalKafkaBroker) -> None:
    _patch_AIOKafkaProducer_init(broker)
    _patch_AIOKafkaProducer_start()
    _patch_AIOKafkaProducer_stop()
    _patch_AIOKafkaProducer_send()
