from functools import partial, wraps
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    TYPE_CHECKING,
)
from contextlib import AsyncExitStack
from inspect import Parameter
import logging

import confluent_kafka
from fast_depends.dependencies import Depends
from typing_extensions import override, Annotated, Doc

from faststream.__about__ import SERVICE_NAME
from faststream.broker.core.broker import BrokerUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
# from faststream.broker.wrapper import FakePublisher, HandlerCallWrapper
from faststream.confluent.asyncapi import Handler, Publisher
from faststream.confluent.client import AsyncConfluentConsumer, AsyncConfluentProducer
from faststream.confluent.message import KafkaMessage
from faststream.confluent.producer import AsyncConfluentFastProducer
from faststream.confluent.security import parse_security
from faststream.broker.utils import get_watcher_context
from faststream.confluent.broker.logging import KafkaLoggingMixin
from faststream.confluent.shared.schemas import ConsumerConnectionParams
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.security import BaseSecurity
from faststream.utils.data import filter_by_dict

if TYPE_CHECKING:
    from faststream.asyncapi import schema as asyncapi
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherMiddleware,
    )
    from faststream.types import SendableMessage

class KafkaBroker(
    KafkaLoggingMixin,
    BrokerUsecase[confluent_kafka.Message, ConsumerConnectionParams],
):
    """KafkaBroker is a class for managing Kafka message consumption and publishing.

    It extends BrokerAsyncUsecase to handle asynchronous operations.

    Args:
        bootstrap_servers (Union[str, Iterable[str]]): Kafka bootstrap server(s).
        protocol (str): The protocol used (default is "kafka").
        protocol_version (str): The Kafka protocol version (default is "auto").
        client_id (str): The client ID for the Kafka client.
        **kwargs: Additional keyword arguments.

    Attributes:
        handlers (Dict[str, Handler]): A dictionary of message handlers.
        _publishers (Dict[str, Publisher]): A dictionary of message publishers.
        _producer (Optional[AsyncConfluentFastProducer]): An optional Kafka producer.

    Methods:
        connect(*args, **kwargs): Establishes a connection to Kafka.
        start(): Starts the KafkaBroker and message handlers.
        publish(*args, **kwargs): Publishes a message to Kafka.
    """

    url: List[str]
    handlers: Dict[str, Handler]
    _publishers: Dict[str, Publisher]
    _producer: Optional[AsyncConfluentFastProducer]

    def __init__(
        self,
        bootstrap_servers: Union[str, Iterable[str]] = "localhost",
        *,
        client_id: str = SERVICE_NAME,
        # broker base args
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Graceful shutdown timeout. Broker waits for all running subscribers completion before shut down."
            ),
        ] = None,
        apply_types: Annotated[
            bool,
            Doc("Whether to use FastDepends or not."),
        ] = True,
        validate: Annotated[
            bool,
            Doc("Whether to cast types using Pydantic validation."),
        ] = True,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[aiokafka.ConsumerRecord]]"],
            Doc("Custom decoder object."),
        ] = None,
        parser: Annotated[
            Optional["CustomParser[aiokafka.ConsumerRecord]"],
            Doc("Custom parser object."),
        ] = None,
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies to apply to all broker subscribers."),
        ] = (),
        middlewares: Annotated[
            Iterable["BrokerMiddleware[aiokafka.ConsumerRecord]"],
            Doc("Middlewares to apply to all broker publishers/subscribers."),
        ] = (),
        # AsyncAPI args
        security: Annotated[
            Optional["BaseSecurity"],
            Doc(
                "Security options to connect broker and generate AsyncAPI server security information."
            ),
        ] = None,
        asyncapi_url: Annotated[
            Union[str, Iterable[str], None],
            Doc("AsyncAPI hardcoded server addresses. Use `servers` if not specified."),
        ] = None,
        protocol: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol."),
        ] = None,
        protocol_version: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol version."),
        ] = "auto",
        description: Annotated[
            Optional[str],
            Doc("AsyncAPI server description."),
        ] = None,
        tags: Annotated[
            Optional[Iterable[Union["asyncapi.Tag", "asyncapi.TagDict"]]],
            Doc("AsyncAPI server tags."),
        ] = None,
        # logging args
        logger: Annotated[
            Union[logging.Logger, None, object],
            Doc("User specified logger to pass into Context and log service messages."),
        ] = Parameter.empty,
        log_level: Annotated[
            int,
            Doc("Service messages log level."),
        ] = logging.INFO,
        log_fmt: Annotated[
            Optional[str],
            Doc("Default logger log format."),
        ] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a KafkaBroker instance.

        Args:
            bootstrap_servers (Union[str, Iterable[str]]): Kafka bootstrap server(s).
            protocol (str): The protocol used (default is "kafka").
            protocol_version (str): The Kafka protocol version (default is "auto").
            client_id (str): The client ID for the Kafka client.
            security (Optional[BaseSecurity]): Security protocol to use in communication with the broker (default is None).
            **kwargs: Additional keyword arguments.
        """
        if protocol is None:
            if security is not None and security.use_ssl:
                protocol = "kafka-secure"
            else:
                protocol = "kafka"

        servers = [bootstrap_servers] if isinstance(bootstrap_servers, str) else list(bootstrap_servers)

        if asyncapi_url is not None:
            if isinstance(asyncapi_url, str):
                asyncapi_url = [asyncapi_url]
            else:
                asyncapi_url = list(asyncapi_url)
        else:
            asyncapi_url = servers

        super().__init__(
            bootstrap_servers=servers,
            client_id=client_id,
            **kwargs,
            # Basic args
            ## broker base
            graceful_timeout=graceful_timeout,
            apply_types=apply_types,
            validate=validate,
            dependencies=dependencies,
            decoder=decoder,
            parser=parser,
            middlewares=middlewares,
            ## AsyncAPI
            description=description,
            asyncapi_url=asyncapi_url,
            protocol=protocol,
            protocol_version=protocol_version,
            security=security,
            tags=tags,
            ## logging
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
        )
        self.client_id = client_id
        self._producer = None

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[TracebackType] = None,
    ) -> None:
        """Close the KafkaBroker, stopping the producer and cleaning up resources.

        Args:
            exc_type (Optional[Type[BaseException]]): The exception type.
            exc_val (Optional[BaseException]]): The exception value.
            exc_tb (Optional[TracebackType]]): The traceback.
        """
        if self._producer is not None:  # pragma: no branch
            await self._producer.stop()
            self._producer = None

        await super()._close(exc_type, exc_val, exc_tb)

    async def connect(
        self,
        bootstrap_servers: Annotated[
            Union[str, Iterable[str], object],
            Doc("Kafka addresses to connect."),
        ] = Parameter.empty,
        **kwargs: Any,
    ) -> ConsumerConnectionParams:
        if bootstrap_servers is not Parameter.empty:
            kwargs["servers"] = bootstrap_servers

        connection = await super().connect(**kwargs)

        for p in self._publishers.values():
            p._producer = self._producer
            p.client_id = self.client_id

        return connection

    @override
    async def _connect(  # type: ignore[override]
        self,
        *,
        client_id: str,
        **kwargs: Any,
    ) -> ConsumerConnectionParams:
        """Connects to Kafka, initializes the producer, and returns connection parameters.

        Args:
            client_id (str): The client ID.
            **kwargs: Additional keyword arguments.

        Returns:
            ConsumerConnectionParams: The connection parameters.
        """
        security_params = parse_security(self.security)
        producer = AsyncConfluentProducer(
            **kwargs, **security_params, client_id=client_id
        )
        await producer.start()
        self._producer = AsyncConfluentFastProducer(
            producer=producer,
        )
        return filter_by_dict(ConsumerConnectionParams, {**kwargs, **security_params})

    async def start(self) -> None:
        """Start the KafkaBroker and message handlers."""
        await super().start()

        for handler in self.handlers.values():
            self._log(
                f"`{handler.call_name}` waiting for messages",
                extra=handler.get_log_context(None),
            )

            await handler.start(self._producer, **(self._connection or {}))

    @override
    def subscriber(  # type: ignore[override]
        self,
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
        partition_assignment_strategy: Sequence[str] = ("roundrobin",),
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
        parser = None,
        decoder = None,
        middlewares: Optional[
            Sequence[
                Callable[
                    [confluent_kafka.Message],
                    BaseMiddleware,
                ]
            ]
        ] = None,
        filter = default_filter,
        batch: bool = False,
        max_records: Optional[int] = None,
        batch_timeout_ms: int = 200,
        no_ack: bool = False,
        retry: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        get_dependent: Optional[Any] = None,
    ):
        """Create a message subscriber for the specified topics."""
        super().subscriber()

        self._setup_log_context(topics, group_id)

        if not auto_commit and not group_id:
            raise ValueError("You should install `group_id` with manual commit mode")

        key = Handler.get_routing_hash(topics, group_id)
        builder = partial(
            AsyncConfluentConsumer,
            key_deserializer=key_deserializer,
            value_deserializer=value_deserializer,
            fetch_max_wait_ms=fetch_max_wait_ms,
            fetch_max_bytes=fetch_max_bytes,
            fetch_min_bytes=fetch_min_bytes,
            max_partition_fetch_bytes=max_partition_fetch_bytes,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=auto_commit,
            auto_commit_interval_ms=auto_commit_interval_ms,
            check_crcs=check_crcs,
            partition_assignment_strategy=partition_assignment_strategy,
            max_poll_interval_ms=max_poll_interval_ms,
            rebalance_timeout_ms=rebalance_timeout_ms,
            session_timeout_ms=session_timeout_ms,
            heartbeat_interval_ms=heartbeat_interval_ms,
            consumer_timeout_ms=consumer_timeout_ms,
            max_poll_records=max_poll_records,
            exclude_internal_topics=exclude_internal_topics,
            isolation_level=isolation_level,
        )
        self.handlers[key] = handler = self.handlers.get(
            key,
            Handler(
                *topics,
                log_context_builder=partial(
                    self._get_log_context,
                    topics=topics,
                    group_id=group_id,
                ),
                is_manual=not auto_commit,
                group_id=group_id,
                client_id=self.client_id,
                builder=builder,
                batch=batch,
                batch_timeout_ms=batch_timeout_ms,
                max_records=max_records,
                # base options
                graceful_timeout=self.graceful_timeout,
                middlewares=self.middlewares,
                watcher=get_watcher_context(self.logger, no_ack, retry),
                extra_context={},
                # AsyncAPI
                title_=title,
                description_=description,
                include_in_schema=include_in_schema,
            ),
        )

        return handler.add_call(
            filter=filter,
            parser=parser or self._global_parser,
            decoder=decoder or self._global_decoder,
            dependencies=(*self.dependencies, *dependencies),
            middlewares=middlewares,
            # wrapper kwargs
            is_validate=self._is_validate,
            apply_types=self._is_apply_types,
            get_dependent=get_dependent,
        )

    @override
    def publisher(  # type: ignore[override]
        self,
        topic: str,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        batch: bool = False,
        # specific
        middlewares: Iterable["PublisherMiddleware"] = (),
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> Publisher:
        """Create a message publisher for the specified topic."""
        if batch and key:
            raise ValueError("You can't setup `key` with batch publisher")

        publisher = self._publishers.get(topic) or Publisher.create(
            # batch flag
            batch=batch,
            # default args
            key=key,
            # both args
            topic=topic,
            client_id=self.client_id,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=headers,
            reply_to=reply_to,
            # publisher-specific
            middlewares=middlewares,
            # AsyncAPI
            title_=title,
            description_=description,
            schema_=schema,
            include_in_schema=include_in_schema,
        )

        super().publisher(topic, publisher)
        if self._producer is not None:
            publisher._producer = self._producer

        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "SendableMessage",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        async with AsyncExitStack() as stack:
            for m in self.middlewares:
                message = await stack.enter_async_context(
                    m().publish_scope(message, *args, **kwargs)
                )

            assert self._producer, NOT_CONNECTED_YET  # nosec B101
            return await self._producer.publish(message, *args, **kwargs)

    async def publish_batch(
        self,
        *messages: "SendableMessage",
        **kwargs: Any,
    ) -> None:
        async with AsyncExitStack() as stack:
            wrapped_messages = [
                await stack.enter_async_context(
                    middleware().publish_scope(msg, **kwargs)
                )
                for msg in messages
                for middleware in self.middlewares
            ] or messages

            assert self._producer, NOT_CONNECTED_YET  # nosec B101
            await self._producer.publish_batch(*wrapped_messages, **kwargs)
