from typing import Any, Callable, Literal, Sequence, overload

import aiokafka
from fast_depends.dependencies import Depends
from kafka.coordinator.assignors.abstract import AbstractPartitionAssignor
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor

from faststream.broker.core.asynchronous import default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import CustomDecoder, CustomParser, Filter, T_HandlerReturn
from faststream.kafka.message import KafkaMessage

class KafkaRoute:
    """Delayed `KafkaBroker.subscriber()` registration object."""

    @overload
    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        *topics: str,
        group_id: str | None = None,
        key_deserializer: Callable[[bytes], Any] | None = None,
        value_deserializer: Callable[[bytes], Any] | None = None,
        fetch_max_wait_ms: int = 500,
        fetch_max_bytes: int = 52428800,
        fetch_min_bytes: int = 1,
        max_partition_fetch_bytes: int = 1 * 1024 * 1024,
        auto_offset_reset: Literal[
            "latest",
            "earliest",
            "none",
        ] = "latest",
        auto_commit: bool = True,
        auto_commit_interval_ms: int = 5000,
        check_crcs: bool = True,
        partition_assignment_strategy: Sequence[AbstractPartitionAssignor] = (
            RoundRobinPartitionAssignor,
        ),
        max_poll_interval_ms: int = 300000,
        rebalance_timeout_ms: int | None = None,
        session_timeout_ms: int = 10000,
        heartbeat_interval_ms: int = 3000,
        consumer_timeout_ms: int = 200,
        max_poll_records: int | None = None,
        exclude_internal_topics: bool = True,
        isolation_level: Literal[
            "read_uncommitted",
            "read_committed",
        ] = "read_uncommitted",
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: CustomParser[tuple[aiokafka.ConsumerRecord, ...], KafkaMessage]
        | None = None,
        decoder: CustomDecoder[KafkaMessage] | None = None,
        middlewares: Sequence[Callable[[aiokafka.ConsumerRecord], BaseMiddleware]]
        | None = None,
        filter: Filter[
            StreamMessage[tuple[aiokafka.ConsumerRecord, ...]]
        ] = default_filter,
        batch: Literal[True] = True,
        max_records: int | None = None,
        batch_timeout_ms: int = 200,
        retry: bool | int = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> None: ...
    @overload
    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        *topics: str,
        group_id: str | None = None,
        key_deserializer: Callable[[bytes], Any] | None = None,
        value_deserializer: Callable[[bytes], Any] | None = None,
        fetch_max_wait_ms: int = 500,
        fetch_max_bytes: int = 52428800,
        fetch_min_bytes: int = 1,
        max_partition_fetch_bytes: int = 1 * 1024 * 1024,
        auto_offset_reset: Literal[
            "latest",
            "earliest",
            "none",
        ] = "latest",
        auto_commit: bool = True,
        auto_commit_interval_ms: int = 5000,
        check_crcs: bool = True,
        partition_assignment_strategy: Sequence[AbstractPartitionAssignor] = (
            RoundRobinPartitionAssignor,
        ),
        max_poll_interval_ms: int = 300000,
        rebalance_timeout_ms: int | None = None,
        session_timeout_ms: int = 10000,
        heartbeat_interval_ms: int = 3000,
        consumer_timeout_ms: int = 200,
        max_poll_records: int | None = None,
        exclude_internal_topics: bool = True,
        isolation_level: Literal[
            "read_uncommitted",
            "read_committed",
        ] = "read_uncommitted",
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: CustomParser[aiokafka.ConsumerRecord, KafkaMessage] | None = None,
        decoder: CustomDecoder[KafkaMessage] | None = None,
        middlewares: Sequence[Callable[[aiokafka.ConsumerRecord], BaseMiddleware]]
        | None = None,
        filter: Filter[KafkaMessage] = default_filter,
        batch: Literal[False] = False,
        max_records: int | None = None,
        batch_timeout_ms: int = 200,
        retry: bool | int = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        **__service_kwargs: Any,
    ) -> None: ...
