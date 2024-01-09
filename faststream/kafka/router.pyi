from typing import Any, Callable, Literal, Sequence, TypeVar

import aiokafka
from fast_depends.dependencies import Depends
from kafka.coordinator.assignors.abstract import AbstractPartitionAssignor
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
from typing_extensions import override

from faststream.broker.core.asynchronous import default_filter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.router import BrokerRouter
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.kafka.asyncapi import Publisher
from faststream.kafka.message import KafkaMessage
from faststream.kafka.shared.router import KafkaRoute

Partition = TypeVar("Partition")

class KafkaRouter(BrokerRouter[str, aiokafka.ConsumerRecord]):
    _publishers: dict[str, Publisher]  # type: ignore[assignment]

    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[KafkaRoute] = (),
        *,
        dependencies: Sequence[Depends] = (),
        middlewares: Sequence[Callable[[aiokafka.ConsumerRecord], BaseMiddleware]]
        | None = None,
        parser: CustomParser[aiokafka.ConsumerRecord, KafkaMessage] | None = None,
        decoder: CustomDecoder[KafkaMessage] | None = None,
        include_in_schema: bool = True,
    ) -> None: ...
    @override
    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> str: ...  # type: ignore[override]
    @override
    @staticmethod
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher: ...
    @override
    def publisher(  # type: ignore[override]
        self,
        topic: str,
        key: bytes | None = None,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: dict[str, str] | None = None,
        reply_to: str = "",
        batch: bool = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        schema: Any | None = None,
        include_in_schema: bool = True,
    ) -> Publisher: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
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
        batch: bool = False,
        max_records: int | None = None,
        batch_timeout_ms: int = 200,
        retry: bool | int = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[aiokafka.ConsumerRecord, P_HandlerParams, T_HandlerReturn],
    ]: ...
