from functools import partial, wraps
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

import aiokafka
from fast_depends.dependencies import Depends
from kafka.coordinator.assignors.abstract import AbstractPartitionAssignor
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor

from faststream.__about__ import __version__
from faststream._compat import override
from faststream.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.push_back_watcher import BaseWatcher, WatcherContext
from faststream.broker.security import BaseSecurity
from faststream.broker.types import (
    AsyncPublisherProtocol,
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import FakePublisher, HandlerCallWrapper
from faststream.kafka.asyncapi import Handler, Publisher
from faststream.kafka.message import KafkaMessage
from faststream.kafka.producer import AioKafkaFastProducer
from faststream.kafka.security import parse_security
from faststream.kafka.shared.logging import KafkaLoggingMixin
from faststream.kafka.shared.schemas import ConsumerConnectionParams
from faststream.utils import context
from faststream.utils.data import filter_by_dict


class KafkaBroker(
    KafkaLoggingMixin,
    BrokerAsyncUsecase[aiokafka.ConsumerRecord, ConsumerConnectionParams],
):
    """
    KafkaBroker is a class for managing Kafka message consumption and publishing.
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
        _producer (Optional[AioKafkaFastProducer]): An optional Kafka producer.

    Methods:
        connect(*args, **kwargs): Establishes a connection to Kafka.
        start(): Starts the KafkaBroker and message handlers.
        publish(*args, **kwargs): Publishes a message to Kafka.
    """

    handlers: Dict[str, Handler]  # type: ignore[assignment]
    _publishers: Dict[str, Publisher]  # type: ignore[assignment]
    _producer: Optional[AioKafkaFastProducer]

    def __init__(
        self,
        bootstrap_servers: Union[str, Iterable[str]] = "localhost",
        *,
        protocol: Optional[str] = None,
        protocol_version: str = "auto",
        client_id: str = "faststream-" + __version__,
        security: Optional[BaseSecurity] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a KafkaBroker instance.

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

        super().__init__(
            url=bootstrap_servers,
            protocol=protocol,
            protocol_version=protocol_version,
            security=security,
            **kwargs,
            client_id=client_id,
            bootstrap_servers=bootstrap_servers,
        )
        self.client_id = client_id
        self._producer = None

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        """
        Close the KafkaBroker, stopping the producer and cleaning up resources.

        Args:
            exc_type (Optional[Type[BaseException]]): The exception type.
            exc_val (Optional[BaseException]]): The exception value.
            exec_tb (Optional[TracebackType]]): The traceback.
        """
        if self._producer is not None:  # pragma: no branch
            await self._producer.stop()
            self._producer = None

        await super()._close(exc_type, exc_val, exec_tb)

    async def connect(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> ConsumerConnectionParams:
        """
        Establishes a connection to Kafka and returns connection parameters.

        Args:
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            ConsumerConnectionParams: The connection parameters.
        """
        connection = await super().connect(*args, **kwargs)
        for p in self._publishers.values():
            p._producer = self._producer
        return connection

    @override
    async def _connect(  # type: ignore[override]
        self,
        *,
        client_id: str,
        **kwargs: Any,
    ) -> ConsumerConnectionParams:
        """
        Connects to Kafka, initializes the producer, and returns connection parameters.

        Args:
            client_id (str): The client ID.
            **kwargs: Additional keyword arguments.

        Returns:
            ConsumerConnectionParams: The connection parameters.
        """
        security_params = parse_security(self.security)
        producer = aiokafka.AIOKafkaProducer(
            **kwargs, **security_params, client_id=client_id
        )
        await producer.start()
        self._producer = AioKafkaFastProducer(
            producer=producer,
        )
        return filter_by_dict(ConsumerConnectionParams, {**kwargs, **security_params})

    async def start(self) -> None:
        """
        Start the KafkaBroker and message handlers.
        """
        context.set_local(
            "log_context",
            self._get_log_context(None, ""),
        )

        await super().start()

        for handler in self.handlers.values():
            c = self._get_log_context(None, handler.topics)

            if (name := handler.name) is True:
                name = handler.call_name

            self._log(f"`{name}` waiting for messages", extra=c)
            await handler.start(**(self._connection or {}))

    def _process_message(
        self,
        func: Callable[[KafkaMessage], Awaitable[T_HandlerReturn]],
        watcher: BaseWatcher,
    ) -> Callable[[KafkaMessage], Awaitable[WrappedReturn[T_HandlerReturn]],]:
        """
        Wrap a message processing function with a watcher and publisher.

        Args:
            func (Callable[[KafkaMessage], Awaitable[T_HandlerReturn]]): The message processing function.
            watcher (BaseWatcher): The message watcher.

        Returns:
            Callable[[KafkaMessage], Awaitable[WrappedReturn[T_HandlerReturn]]]: The wrapped message processing function.
        """

        @wraps(func)
        async def process_wrapper(
            message: KafkaMessage,
        ) -> WrappedReturn[T_HandlerReturn]:
            """Asynchronously process a Kafka message and wrap the return value.

            Args:
                message (KafkaMessage): The Kafka message to process.

            Returns:
                WrappedReturn[T_HandlerReturn]: The wrapped return value.

            Raises:
                AssertionError: If the code reaches an unreachable point.
            !!! note

                The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
            """
            async with WatcherContext(watcher, message):
                r = await self._execute_handler(func, message)

                pub_response: Optional[AsyncPublisherProtocol]
                if message.reply_to:
                    pub_response = FakePublisher(
                        partial(self.publish, topic=message.reply_to)
                    )
                else:
                    pub_response = None

                return r, pub_response

            raise AssertionError("unreachable")

        return process_wrapper

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
        enable_auto_commit: bool = True,
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
            Union[
                CustomParser[aiokafka.ConsumerRecord],
                CustomParser[Tuple[aiokafka.ConsumerRecord, ...]],
            ]
        ] = None,
        decoder: Optional[
            Union[
                CustomDecoder[aiokafka.ConsumerRecord],
                CustomDecoder[Tuple[aiokafka.ConsumerRecord, ...]],
            ]
        ] = None,
        middlewares: Optional[
            Sequence[
                Callable[
                    [aiokafka.ConsumerRecord],
                    BaseMiddleware,
                ]
            ]
        ] = None,
        filter: Union[
            Filter[KafkaMessage],
            Filter[StreamMessage[Tuple[aiokafka.ConsumerRecord, ...]]],
        ] = default_filter,
        batch: bool = False,
        max_records: Optional[int] = None,
        batch_timeout_ms: int = 200,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **original_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        Union[
            HandlerCallWrapper[
                aiokafka.ConsumerRecord, P_HandlerParams, T_HandlerReturn
            ],
            HandlerCallWrapper[
                Tuple[aiokafka.ConsumerRecord, ...], P_HandlerParams, T_HandlerReturn
            ],
        ],
    ]:
        """
        Create a message subscriber for the specified topics.

        Args:
            *topics (str): The topics to subscribe to.
            group_id (Optional[str]): The Kafka consumer group ID.
            key_deserializer (Optional[Callable[[bytes], Any]]): Key deserializer function.
            value_deserializer (Optional[Callable[[bytes], Any]]): Value deserializer function.
            fetch_max_wait_ms (int): The maximum time to wait for data.
            fetch_max_bytes (int): The maximum number of bytes to fetch.
            fetch_min_bytes (int): The minimum number of bytes to fetch.
            max_partition_fetch_bytes (int): The maximum bytes to fetch for a partition.
            auto_offset_reset (Literal["latest", "earliest", "none"]): Auto offset reset policy.
            enable_auto_commit (bool): Whether to enable auto-commit.
            auto_commit_interval_ms (int): Auto-commit interval in milliseconds.
            check_crcs (bool): Whether to check CRCs.
            partition_assignment_strategy (Sequence[AbstractPartitionAssignor]): Partition assignment strategy.
            max_poll_interval_ms (int): Maximum poll interval in milliseconds.
            rebalance_timeout_ms (Optional[int]): Rebalance timeout in milliseconds.
            session_timeout_ms (int): Session timeout in milliseconds.
            heartbeat_interval_ms (int): Heartbeat interval in milliseconds.
            consumer_timeout_ms (int): Consumer timeout in milliseconds.
            max_poll_records (Optional[int]): Maximum number of records to poll.
            exclude_internal_topics (bool): Whether to exclude internal topics.
            isolation_level (Literal["read_uncommitted", "read_committed"]): Isolation level.
            dependencies (Sequence[Depends]): Additional dependencies for message handling.
            parser (Optional[Union[CustomParser[aiokafka.ConsumerRecord], CustomParser[Tuple[aiokafka.ConsumerRecord, ...]]]]): Message parser.
            decoder (Optional[Union[CustomDecoder[aiokafka.ConsumerRecord], CustomDecoder[Tuple[aiokafka.ConsumerRecord, ...]]]]): Message decoder.
            middlewares (Optional[Sequence[Callable[[aiokafka.ConsumerRecord], BaseMiddleware]]]): Message middlewares.
            filter (Union[Filter[KafkaMessage], Filter[StreamMessage[Tuple[aiokafka.ConsumerRecord, ...]]]]): Message filter.
            batch (bool): Whether to process messages in batches.
            max_records (Optional[int]): Maximum number of records to process in each batch.
            batch_timeout_ms (int): Batch timeout in milliseconds.
            title (Optional[str]): AsyncAPI title.
            description (Optional[str]): AsyncAPI description.
            **original_kwargs: Additional keyword arguments.

        Returns:
            Callable: A decorator that wraps a message handler function.
        """
        super().subscriber()

        self._setup_log_context(topics)

        key = "".join(topics)
        builder = partial(
            aiokafka.AIOKafkaConsumer,
            key_deserializer=key_deserializer,
            value_deserializer=value_deserializer,
            fetch_max_wait_ms=fetch_max_wait_ms,
            fetch_max_bytes=fetch_max_bytes,
            fetch_min_bytes=fetch_min_bytes,
            max_partition_fetch_bytes=max_partition_fetch_bytes,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
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
        handler = self.handlers.get(
            key,
            Handler(
                *topics,
                group_id=group_id,
                client_id=self.client_id,
                builder=builder,
                description=description,
                title=title,
                batch=batch,
                batch_timeout_ms=batch_timeout_ms,
                max_records=max_records,
            ),
        )

        self.handlers[key] = handler

        def consumer_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> HandlerCallWrapper[
            aiokafka.ConsumerRecord, P_HandlerParams, T_HandlerReturn
        ]:
            """A wrapper function for a consumer handler.

            Args:
                func : The consumer handler function to be wrapped.

            Returns:
                The wrapped handler call.

            Raises:
                NotImplementedError: If silent animals are not supported.
            !!! note

                The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
            """
            handler_call, dependant = self._wrap_handler(
                func=func,
                extra_dependencies=dependencies,
                **original_kwargs,
                topics=topics,
            )

            handler.add_call(
                handler=handler_call,
                filter=filter,
                middlewares=middlewares,
                parser=parser or self._global_parser,
                decoder=decoder or self._global_decoder,
                dependant=dependant,
            )

            return handler_call

        return consumer_wrapper

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
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Publisher:
        """
        Create a message publisher for the specified topic.

        Args:
            topic (str): The topic to publish messages to.
            key (Optional[bytes]): Message key.
            partition (Optional[int]): Partition to send the message to.
            timestamp_ms (Optional[int]): Message timestamp in milliseconds.
            headers (Optional[Dict[str, str]]): Message headers.
            reply_to (str): The topic to which responses should be sent.
            batch (bool): Whether to publish messages in batches.
            title (Optional[str]): AsyncAPI title.
            description (Optional[str]): AsyncAPI description.

        Returns:
            Publisher: A message publisher.
        """
        publisher = self._publishers.get(
            topic,
            Publisher(
                topic=topic,
                client_id=self.client_id,
                key=key,
                batch=batch,
                partition=partition,
                timestamp_ms=timestamp_ms,
                headers=headers,
                reply_to=reply_to,
                title=title,
                _description=description,
            ),
        )
        super().publisher(topic, publisher)
        return publisher

    @override
    async def publish(  # type: ignore[override]
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Publish a message to Kafka.

        Args:
            *args: Positional arguments for message publishing.
            **kwargs: Keyword arguments for message publishing.

        Raises:
            RuntimeError: If KafkaBroker is not started yet.
        """
        assert self._producer, "KafkaBroker is not started yet"  # nosec B101
        return await self._producer.publish(*args, **kwargs)

    async def publish_batch(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Publish a batch of messages to Kafka.

        Args:
            *args: Positional arguments for message publishing.
            **kwargs: Keyword arguments for message publishing.

        Raises:
            RuntimeError: If KafkaBroker is not started yet.
        """
        assert self._producer, "KafkaBroker is not started yet"  # nosec B101
        await self._producer.publish_batch(*args, **kwargs)
