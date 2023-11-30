from typing import Any, Callable, Literal, Optional, Sequence, Tuple, Union, overload

import aiokafka
from fast_depends.dependencies import Depends
from kafka.coordinator.assignors.abstract import AbstractPartitionAssignor
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor

from faststream.broker.core.asyncronous import default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import CustomDecoder, CustomParser, Filter, T_HandlerReturn
from faststream.kafka.message import KafkaMessage

class KafkaRoute:
    """Delayed `KafkaBroker.subscriber()` registration object"""

    @overload
    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        *topics: str,
        group_id: Optional[str] = None,
        key_deserializer: Optional[Callable[[bytes], Any]] = None,
        value_deserializer: Optional[Callable[[bytes], Any]] = None,
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
        rebalance_timeout_ms: Optional[int] = None,
        session_timeout_ms: int = 10000,
        heartbeat_interval_ms: int = 3000,
        consumer_timeout_ms: int = 200,
        max_poll_records: Optional[int] = None,
        exclude_internal_topics: bool = True,
        isolation_level: Literal[
            "read_uncommitted",
            "read_committed",
        ] = "read_uncommitted",
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[
            CustomParser[Tuple[aiokafka.ConsumerRecord, ...], KafkaMessage]
        ] = None,
        decoder: Optional[CustomDecoder[KafkaMessage]] = None,
        middlewares: Optional[
            Sequence[
                Callable[
                    [aiokafka.ConsumerRecord],
                    BaseMiddleware,
                ]
            ]
        ] = None,
        filter: Filter[
            StreamMessage[Tuple[aiokafka.ConsumerRecord, ...]]
        ] = default_filter,
        batch: Literal[True] = True,
        max_records: Optional[int] = None,
        batch_timeout_ms: int = 200,
        retry: Union[bool, int] = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> None: ...
    @overload
    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        *topics: str,
        group_id: Optional[str] = None,
        key_deserializer: Optional[Callable[[bytes], Any]] = None,
        value_deserializer: Optional[Callable[[bytes], Any]] = None,
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
        rebalance_timeout_ms: Optional[int] = None,
        session_timeout_ms: int = 10000,
        heartbeat_interval_ms: int = 3000,
        consumer_timeout_ms: int = 200,
        max_poll_records: Optional[int] = None,
        exclude_internal_topics: bool = True,
        isolation_level: Literal[
            "read_uncommitted",
            "read_committed",
        ] = "read_uncommitted",
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[aiokafka.ConsumerRecord, KafkaMessage]] = None,
        decoder: Optional[CustomDecoder[KafkaMessage]] = None,
        middlewares: Optional[
            Sequence[
                Callable[
                    [aiokafka.ConsumerRecord],
                    BaseMiddleware,
                ]
            ]
        ] = None,
        filter: Filter[KafkaMessage] = default_filter,
        batch: Literal[False] = False,
        max_records: Optional[int] = None,
        batch_timeout_ms: int = 200,
        retry: Union[bool, int] = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **__service_kwargs: Any,
    ) -> None: ...
