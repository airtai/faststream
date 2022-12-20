# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/aiokafka_playground.ipynb.

# %% auto 0
__all__ = ['logger', 'process_msgs', 'process_message_callback', 'aiokafka_consumer_loop']

# %% ../../nbs/aiokafka_playground.ipynb 1
from typing import *

from os import environ
import asyncio
from unittest.mock import MagicMock, Mock, call
from datetime import datetime, timedelta

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import TopicPartition, ConsumerRecord
from pydantic import BaseModel, HttpUrl, NonNegativeInt, Field
import asyncer
import anyio

from ..logger import get_logger, supress_timestamps
from fast_kafka_api.testing import (
    true_after,
    create_and_fill_testing_topic,
    nb_safe_seed,
)

# %% ../../nbs/aiokafka_playground.ipynb 4
logger = get_logger(__name__)

# %% ../../nbs/aiokafka_playground.ipynb 8
async def process_msgs(
    *,
    msgs: Dict[TopicPartition, List[ConsumerRecord]],
    callbacks: Dict[str, Callable[[BaseModel], None]],
    msg_types: Dict[str, Type[BaseModel]],
    process_f: Callable[[Callable[[BaseModel], None], BaseModel], None]
):
    for topic_partition, topic_msgs in msgs.items():
        topic = topic_partition.topic
        msg_type = msg_types[topic]
        decoded_msgs = [
            msg_type.parse_raw(msg.value.decode("utf-8")) for msg in topic_msgs
        ]
        for msg in decoded_msgs:
            await process_f((callbacks[topic], msg))

# %% ../../nbs/aiokafka_playground.ipynb 14
async def process_message_callback(receive_stream):
    async with receive_stream:
        async for callback, msg in receive_stream:
            await callback(msg)


async def _aiokafka_consumer_loop(
    *,
    consumer: AIOKafkaConsumer,
    max_buffer_size: int,
    callbacks: Dict[str, Callable[[BaseModel], None]],
    msg_types: Dict[str, Type[BaseModel]],
    is_shutting_down_f: Callable[[], bool],
):
    send_stream, receive_stream = anyio.create_memory_object_stream(
        max_buffer_size=max_buffer_size
    )
    async with anyio.create_task_group() as tg:
        tg.start_soon(process_message_callback, receive_stream)
        async with send_stream:
            while True:
                msgs = await consumer.getmany(timeout_ms=100)
                await process_msgs(
                    msgs=msgs,
                    callbacks=callbacks,
                    msg_types=msg_types,
                    process_f=send_stream.send,
                )
                if is_shutting_down_f():
                    break

# %% ../../nbs/aiokafka_playground.ipynb 16
async def aiokafka_consumer_loop(
    topics: List[str],
    *,
    bootstrap_servers: str,
    auto_offset_reset: str,
    max_poll_records: int,
    max_buffer_size: int,
    callbacks: Dict[str, Callable[[BaseModel], None]],
    msg_types: Dict[str, Type[BaseModel]],
    is_shutting_down_f: Callable[[], bool],
):
    consumer = AIOKafkaConsumer(
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset=auto_offset_reset,
        max_poll_records=max_poll_records,
    )
    logger.info("Consumer created.")

    await consumer.start()
    logger.info("Consumer started.")
    consumer.subscribe(topics)
    logger.info("Consumer subscribed.")

    try:
        await _aiokafka_consumer_loop(
            consumer=consumer,
            max_buffer_size=max_buffer_size,
            callbacks=callbacks,
            msg_types=msg_types,
            is_shutting_down_f=is_shutting_down_f,
        )
    finally:
        await consumer.stop()
        logger.info(f"Consumer stopped.")
