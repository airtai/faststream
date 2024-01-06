import logging
from asyncio import AbstractEventLoop
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    Literal,
    Mapping,
    Sequence,
    TypeVar,
    overload,
)

import aiokafka
from aiokafka import ConsumerRecord
from aiokafka.producer.producer import _missing
from fast_depends.dependencies import Depends
from fastapi import params
from fastapi.datastructures import Default
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from kafka.coordinator.assignors.abstract import AbstractPartitionAssignor
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
from kafka.partitioner.default import DefaultPartitioner
from starlette import routing
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, AppType, Lifespan
from typing_extensions import override

from faststream.__about__ import __version__
from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.asynchronous import default_filter
from faststream.broker.fastapi.router import StreamRouter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.security import BaseSecurity
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.kafka.asyncapi import Publisher
from faststream.kafka.broker import KafkaBroker
from faststream.kafka.message import KafkaMessage
from faststream.log import access_logger

Partition = TypeVar("Partition")

class KafkaRouter(StreamRouter[ConsumerRecord]):
    broker_class: type[KafkaBroker]
    broker: KafkaBroker

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
        # FastAPI kwargs
        prefix: str = "",
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        default_response_class: type[Response] = Default(JSONResponse),
        responses: dict[int | str, dict[str, Any]] | None = None,
        callbacks: list[routing.BaseRoute] | None = None,
        routes: list[routing.BaseRoute] | None = None,
        redirect_slashes: bool = True,
        default: ASGIApp | None = None,
        dependency_overrides_provider: Any | None = None,
        route_class: type[APIRoute] = APIRoute,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        lifespan: Lifespan[Any] | None = None,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
        # broker kwargs
        graceful_timeout: float | None = None,
        apply_types: bool = True,
        validate: bool = True,
        decoder: CustomDecoder[KafkaMessage] | None = None,
        parser: CustomParser[aiokafka.ConsumerRecord, KafkaMessage] | None = None,
        middlewares: Sequence[Callable[[aiokafka.ConsumerRecord], BaseMiddleware]]
        | None = None,
        # AsyncAPI information
        asyncapi_url: str | list[str] | None = None,
        protocol: str = "kafka",
        protocol_version: str = "auto",
        description: str | None = None,
        asyncapi_tags: Sequence[asyncapi.Tag] | None = None,
        schema_url: str | None = "/asyncapi",
        setup_state: bool = True,
        # logging args
        logger: logging.Logger | None = access_logger,
        log_level: int = logging.INFO,
        log_fmt: str | None = None,
        **kwargs: Any,
    ) -> None: ...
    @overload  # type: ignore[override]
    @override
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
    @overload  # type: ignore[override]
    @override
    def add_api_mq_route(
        self,
        *topics: str,
        endpoint: Callable[..., T_HandlerReturn],
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
        **__service_kwargs: Any,
    ) -> Callable[
        [tuple[aiokafka.ConsumerRecord, ...], bool], Awaitable[T_HandlerReturn]
    ]: ...
    @overload
    def add_api_mq_route(
        self,
        *topics: str,
        endpoint: Callable[..., T_HandlerReturn],
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
    ) -> Callable[[aiokafka.ConsumerRecord, bool], Awaitable[T_HandlerReturn]]: ...
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
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Mapping[str, Any]],
    ) -> Callable[[AppType], Mapping[str, Any]]: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Awaitable[Mapping[str, Any]]],
    ) -> Callable[[AppType], Awaitable[Mapping[str, Any]]]: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], None],
    ) -> Callable[[AppType], None]: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Awaitable[None]],
    ) -> Callable[[AppType], Awaitable[None]]: ...
    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: KafkaBroker,
        including_broker: KafkaBroker,
    ) -> None: ...
