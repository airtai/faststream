import logging
from asyncio import AbstractEventLoop
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Iterable,
    Literal,
    Sequence,
    TypeVar,
    overload,
)

import aiokafka
from aiokafka.producer.producer import _missing
from fast_depends.dependencies import Depends
from kafka.coordinator.assignors.abstract import AbstractPartitionAssignor
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
from kafka.partitioner.default import DefaultPartitioner
from typing_extensions import override

from faststream.__about__ import __version__
from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.asynchronous import BrokerAsyncUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.security import BaseSecurity
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.kafka.asyncapi import Handler, Publisher
from faststream.kafka.message import KafkaMessage
from faststream.kafka.producer import AioKafkaFastProducer
from faststream.kafka.shared.logging import KafkaLoggingMixin
from faststream.kafka.shared.schemas import ConsumerConnectionParams
from faststream.log import access_logger
from faststream.types import SendableMessage

Partition = TypeVar("Partition")

class KafkaBroker(
    KafkaLoggingMixin,
    BrokerAsyncUsecase[aiokafka.ConsumerRecord, ConsumerConnectionParams],
):
    handlers: dict[str, Handler]
    _publishers: dict[str, Publisher]
    _producer: AioKafkaFastProducer | None

    def __init__(
        self,
        bootstrap_servers: str | Iterable[str] = "localhost",
        *,
        # both
        client_id: str = "faststream-" + __version__,
        request_timeout_ms: int = 40 * 1000,
        retry_backoff_ms: int = 100,
        metadata_max_age_ms: int = 5 * 60 * 1000,
        api_version: str = "auto",
        connections_max_idle_ms: int = 540000,
        security: BaseSecurity | None = None,
        # publisher
        acks: Literal[0, 1, -1, "all"] | object = _missing,
        key_serializer: Callable[[Any], bytes] | None = None,
        value_serializer: Callable[[Any], bytes] | None = None,
        compression_type: Literal["gzip", "snappy", "lz4", "zstd"] | None = None,
        max_batch_size: int = 16384,
        partitioner: Callable[
            [bytes, list[Partition], list[Partition]],
            Partition,
        ] = DefaultPartitioner(),
        max_request_size: int = 1048576,
        linger_ms: int = 0,
        send_backoff_ms: int = 100,
        enable_idempotence: bool = False,
        transactional_id: str | None = None,
        transaction_timeout_ms: int = 60000,
        loop: AbstractEventLoop | None = None,
        # broker args
        graceful_timeout: float | None = None,
        apply_types: bool = True,
        validate: bool = True,
        dependencies: Sequence[Depends] = (),
        decoder: CustomDecoder[KafkaMessage] | None = None,
        parser: CustomParser[aiokafka.ConsumerRecord, KafkaMessage] | None = None,
        middlewares: Sequence[Callable[[aiokafka.ConsumerRecord], BaseMiddleware]]
        | None = None,
        # AsyncAPI information
        asyncapi_url: str | list[str] | None = None,
        protocol: str = "kafka",
        protocol_version: str = "auto",
        description: str | None = None,
        tags: Sequence[asyncapi.Tag] | None = None,
        # logging args
        logger: logging.Logger | None = access_logger,
        log_level: int = logging.INFO,
        log_fmt: str | None = None,
        **kwargs: Any,
    ) -> None: ...
    async def _close(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exec_tb: TracebackType | None = None,
    ) -> None: ...
    async def connect(
        self,
        bootstrap_servers: str | Iterable[str] = "localhost",
        *,
        # both
        client_id: str = "faststream-" + __version__,
        request_timeout_ms: int = 40 * 1000,
        retry_backoff_ms: int = 100,
        metadata_max_age_ms: int = 5 * 60 * 1000,
        api_version: str = "auto",
        connections_max_idle_ms: int = 540000,
        security: BaseSecurity | None = None,
        # publisher
        acks: Literal[0, 1, -1, "all"] | object = _missing,
        key_serializer: Callable[[Any], bytes] | None = None,
        value_serializer: Callable[[Any], bytes] | None = None,
        compression_type: Literal["gzip", "snappy", "lz4", "zstd"] | None = None,
        max_batch_size: int = 16384,
        partitioner: Callable[
            [bytes, list[Partition], list[Partition]],
            Partition,
        ] = DefaultPartitioner(),
        max_request_size: int = 1048576,
        linger_ms: int = 0,
        send_backoff_ms: int = 100,
        enable_idempotence: bool = False,
        transactional_id: str | None = None,
        transaction_timeout_ms: int = 60000,
        loop: AbstractEventLoop | None = None,
    ) -> ConsumerConnectionParams: ...
    @override
    async def _connect(  # type: ignore[override]
        self,
        *,
        bootstrap_servers: str | Iterable[str] = "localhost",
        # both
        client_id: str = "faststream-" + __version__,
        request_timeout_ms: int = 40 * 1000,
        retry_backoff_ms: int = 100,
        metadata_max_age_ms: int = 5 * 60 * 1000,
        api_version: str = "auto",
        connections_max_idle_ms: int = 540000,
        security: BaseSecurity | None = None,
        # publisher
        acks: Literal[0, 1, -1, "all"] | object = _missing,
        key_serializer: Callable[[Any], bytes] | None = None,
        value_serializer: Callable[[Any], bytes] | None = None,
        compression_type: Literal["gzip", "snappy", "lz4", "zstd"] | None = None,
        max_batch_size: int = 16384,
        partitioner: Callable[
            [bytes, list[Partition], list[Partition]],
            Partition,
        ] = DefaultPartitioner(),
        max_request_size: int = 1048576,
        linger_ms: int = 0,
        send_backoff_ms: int = 100,
        enable_idempotence: bool = False,
        transactional_id: str | None = None,
        transaction_timeout_ms: int = 60000,
        loop: AbstractEventLoop | None = None,
    ) -> ConsumerConnectionParams: ...
    async def start(self) -> None: ...
    def _process_message(
        self,
        func: Callable[
            [StreamMessage[aiokafka.ConsumerRecord]], Awaitable[T_HandlerReturn]
        ],
        watcher: Callable[..., AsyncContextManager[None]],
        **kwargs: Any,
    ) -> Callable[
        [StreamMessage[aiokafka.ConsumerRecord]],
        Awaitable[WrappedReturn[T_HandlerReturn]],
    ]: ...
    @override  # type: ignore[override]
    @overload
    def subscriber(
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
        batch: Literal[False] = False,
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
    @overload
    def subscriber(
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
        no_ack: bool = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[
            tuple[aiokafka.ConsumerRecord, ...], P_HandlerParams, T_HandlerReturn
        ],
    ]: ...
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
    async def publish(  # type: ignore[override]
        self,
        message: SendableMessage,
        topic: str,
        key: bytes | None = None,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: dict[str, str] | None = None,
        correlation_id: str | None = None,
        *,
        reply_to: str = "",
    ) -> None: ...
    async def publish_batch(
        self,
        *msgs: SendableMessage,
        topic: str,
        partition: int | None = None,
        timestamp_ms: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None: ...
