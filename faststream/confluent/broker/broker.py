import logging
from collections.abc import Iterable, Sequence
from functools import partial
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Literal,
    Optional,
    TypeVar,
    Union,
)

import anyio
import confluent_kafka
from typing_extensions import Doc, deprecated, override

from faststream.__about__ import SERVICE_NAME
from faststream._internal.broker.broker import BrokerUsecase
from faststream._internal.constants import EMPTY
from faststream._internal.utils.data import filter_by_dict
from faststream.confluent.client import AsyncConfluentConsumer, AsyncConfluentProducer
from faststream.confluent.config import ConfluentFastConfig
from faststream.confluent.publisher.producer import AsyncConfluentFastProducer
from faststream.confluent.response import KafkaPublishCommand
from faststream.confluent.schemas.params import ConsumerConnectionParams
from faststream.confluent.security import parse_security
from faststream.message import gen_cor_id
from faststream.response.publish_type import PublishType

from .logging import make_kafka_logger_state
from .registrator import KafkaRegistrator

if TYPE_CHECKING:
    import asyncio
    from types import TracebackType

    from confluent_kafka import Message
    from fast_depends.dependencies import Dependant
    from fast_depends.library.serializer import SerializerProto

    from faststream._internal.basic_types import (
        AnyDict,
        Decorator,
        LoggerProto,
        SendableMessage,
    )
    from faststream._internal.broker.abc_broker import ABCBroker
    from faststream._internal.types import (
        BrokerMiddleware,
        CustomCallable,
    )
    from faststream.confluent.config import ConfluentConfig
    from faststream.confluent.message import KafkaMessage
    from faststream.security import BaseSecurity
    from faststream.specification.schema.extra import Tag, TagDict

Partition = TypeVar("Partition")


class KafkaBroker(  # type: ignore[misc]
    KafkaRegistrator,
    BrokerUsecase[
        Union[
            confluent_kafka.Message,
            tuple[confluent_kafka.Message, ...],
        ],
        Callable[..., AsyncConfluentConsumer],
    ],
):
    url: list[str]
    _producer: AsyncConfluentFastProducer

    def __init__(
        self,
        bootstrap_servers: Annotated[
            Union[str, Iterable[str]],
            Doc(
                """
            A `host[:port]` string (or list of `host[:port]` strings) that the consumer should contact to bootstrap
            initial cluster metadata.

            This does not have to be the full node list.
            It just needs to have at least one broker that will respond to a
            Metadata API Request. Default port is 9092.
            """,
            ),
        ] = "localhost",
        *,
        # both
        request_timeout_ms: Annotated[
            int,
            Doc("Client request timeout in milliseconds."),
        ] = 40 * 1000,
        retry_backoff_ms: Annotated[
            int,
            Doc("Milliseconds to backoff when retrying on errors."),
        ] = 100,
        metadata_max_age_ms: Annotated[
            int,
            Doc(
                """
            The period of time in milliseconds after
            which we force a refresh of metadata even if we haven't seen any
            partition leadership changes to proactively discover any new
            brokers or partitions.
            """,
            ),
        ] = 5 * 60 * 1000,
        connections_max_idle_ms: Annotated[
            int,
            Doc(
                """
             Close idle connections after the number
            of milliseconds specified by this config. Specifying `None` will
            disable idle checks.
            """,
            ),
        ] = 9 * 60 * 1000,
        client_id: Annotated[
            Optional[str],
            Doc(
                """
            A name for this client. This string is passed in
            each request to servers and can be used to identify specific
            server-side log entries that correspond to this client. Also
            submitted to :class:`~.consumer.group_coordinator.GroupCoordinator`
            for logging with respect to consumer group administration.
            """,
            ),
        ] = SERVICE_NAME,
        allow_auto_create_topics: Annotated[
            bool,
            Doc(
                """
            Allow automatic topic creation on the broker when subscribing to or assigning non-existent topics.
            """,
            ),
        ] = True,
        config: Annotated[
            Optional["ConfluentConfig"],
            Doc(
                """
                Extra configuration for the confluent-kafka-python
                producer/consumer. See `confluent_kafka.Config <https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#kafka-client-configuration>`_.
                """,
            ),
        ] = None,
        # publisher args
        acks: Annotated[
            Literal[0, 1, -1, "all"],
            Doc(
                """
            One of ``0``, ``1``, ``all``. The number of acknowledgments
            the producer requires the leader to have received before considering a
            request complete. This controls the durability of records that are
            sent. The following settings are common:

            * ``0``: Producer will not wait for any acknowledgment from the server
              at all. The message will immediately be added to the socket
              buffer and considered sent. No guarantee can be made that the
              server has received the record in this case, and the retries
              configuration will not take effect (as the client won't
              generally know of any failures). The offset given back for each
              record will always be set to -1.
            * ``1``: The broker leader will write the record to its local log but
              will respond without awaiting full acknowledgement from all
              followers. In this case should the leader fail immediately
              after acknowledging the record but before the followers have
              replicated it then the record will be lost.
            * ``all``: The broker leader will wait for the full set of in-sync
              replicas to acknowledge the record. This guarantees that the
              record will not be lost as long as at least one in-sync replica
              remains alive. This is the strongest available guarantee.

            If unset, defaults to ``acks=1``. If `enable_idempotence` is
            :data:`True` defaults to ``acks=all``.
            """,
            ),
        ] = EMPTY,
        compression_type: Annotated[
            Optional[Literal["gzip", "snappy", "lz4", "zstd"]],
            Doc(
                """
            The compression type for all data generated bythe producer.
            Compression is of full batches of data, so the efficacy of batching
            will also impact the compression ratio (more batching means better
            compression).
            """,
            ),
        ] = None,
        partitioner: Annotated[
            Union[
                str,
                Callable[
                    [bytes, list[Partition], list[Partition]],
                    Partition,
                ],
            ],
            Doc(
                """
            Callable used to determine which partition
            each message is assigned to. Called (after key serialization):
            ``partitioner(key_bytes, all_partitions, available_partitions)``.
            The default partitioner implementation hashes each non-None key
            using the same murmur2 algorithm as the Java client so that
            messages with the same key are assigned to the same partition.
            When a key is :data:`None`, the message is delivered to a random partition
            (filtered to partitions with available leaders only, if possible).
            """,
            ),
        ] = "consistent_random",
        max_request_size: Annotated[
            int,
            Doc(
                """
            The maximum size of a request. This is also
            effectively a cap on the maximum record size. Note that the server
            has its own cap on record size which may be different from this.
            This setting will limit the number of record batches the producer
            will send in a single request to avoid sending huge requests.
            """,
            ),
        ] = 1024 * 1024,
        linger_ms: Annotated[
            int,
            Doc(
                """
            The producer groups together any records that arrive
            in between request transmissions into a single batched request.
            Normally this occurs only under load when records arrive faster
            than they can be sent out. However in some circumstances the client
            may want to reduce the number of requests even under moderate load.
            This setting accomplishes this by adding a small amount of
            artificial delay; that is, if first request is processed faster,
            than `linger_ms`, producer will wait ``linger_ms - process_time``.
            """,
            ),
        ] = 0,
        enable_idempotence: Annotated[
            bool,
            Doc(
                """
            When set to `True`, the producer will
            ensure that exactly one copy of each message is written in the
            stream. If `False`, producer retries due to broker failures,
            etc., may write duplicates of the retried message in the stream.
            Note that enabling idempotence acks to set to ``all``. If it is not
            explicitly set by the user it will be chosen.
            """,
            ),
        ] = False,
        transactional_id: Optional[str] = None,
        transaction_timeout_ms: int = 60 * 1000,
        # broker base args
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Graceful shutdown timeout. Broker waits for all running subscribers completion before shut down.",
            ),
        ] = 15.0,
        decoder: Annotated[
            Optional["CustomCallable"],
            Doc("Custom decoder object."),
        ] = None,
        parser: Annotated[
            Optional["CustomCallable"],
            Doc("Custom parser object."),
        ] = None,
        dependencies: Annotated[
            Iterable["Dependant"],
            Doc("Dependencies to apply to all broker subscribers."),
        ] = (),
        middlewares: Annotated[
            Sequence["BrokerMiddleware[Union[Message, tuple[Message, ...]]]"],
            Doc("Middlewares to apply to all broker publishers/subscribers."),
        ] = (),
        routers: Annotated[
            Sequence["ABCBroker[Message]"],
            Doc("Routers to apply to broker."),
        ] = (),
        # AsyncAPI args
        security: Annotated[
            Optional["BaseSecurity"],
            Doc(
                "Security options to connect broker and generate AsyncAPI server security information.",
            ),
        ] = None,
        specification_url: Annotated[
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
            Iterable[Union["Tag", "TagDict"]],
            Doc("AsyncAPI server tags."),
        ] = (),
        # logging args
        logger: Annotated[
            Optional["LoggerProto"],
            Doc("User specified logger to pass into Context and log service messages."),
        ] = EMPTY,
        log_level: Annotated[
            int,
            Doc("Service messages log level."),
        ] = logging.INFO,
        log_fmt: Annotated[
            Optional[str],
            deprecated("Use `logger` instead. Will be removed in the 0.7.0 release."),
            Doc("Default logger log format."),
        ] = None,
        # FastDepends args
        apply_types: Annotated[
            bool,
            Doc("Whether to use FastDepends or not."),
        ] = True,
        serializer: Optional["SerializerProto"] = EMPTY,
        _get_dependant: Annotated[
            Optional[Callable[..., Any]],
            Doc("Custom library dependant generator callback."),
        ] = None,
        _call_decorators: Annotated[
            Iterable["Decorator"],
            Doc("Any custom decorator to apply to wrapped functions."),
        ] = (),
    ) -> None:
        if protocol is None:
            if security is not None and security.use_ssl:
                protocol = "kafka-secure"
            else:
                protocol = "kafka"

        servers = (
            [bootstrap_servers]
            if isinstance(bootstrap_servers, str)
            else list(bootstrap_servers)
        )

        if specification_url is not None:
            if isinstance(specification_url, str):
                specification_url = [specification_url]
            else:
                specification_url = list(specification_url)
        else:
            specification_url = servers

        super().__init__(
            bootstrap_servers=servers,
            # both args
            client_id=client_id,
            request_timeout_ms=request_timeout_ms,
            retry_backoff_ms=retry_backoff_ms,
            metadata_max_age_ms=metadata_max_age_ms,
            allow_auto_create_topics=allow_auto_create_topics,
            connections_max_idle_ms=connections_max_idle_ms,
            # publisher args
            acks=acks,
            compression_type=compression_type,
            partitioner=partitioner,
            max_request_size=max_request_size,
            linger_ms=linger_ms,
            enable_idempotence=enable_idempotence,
            transactional_id=transactional_id,
            transaction_timeout_ms=transaction_timeout_ms,
            # Basic args
            graceful_timeout=graceful_timeout,
            dependencies=dependencies,
            decoder=decoder,
            parser=parser,
            middlewares=middlewares,
            routers=routers,
            # AsyncAPI args
            description=description,
            specification_url=specification_url,
            protocol=protocol,
            protocol_version=protocol_version,
            security=security,
            tags=tags,
            # Logging args
            logger_state=make_kafka_logger_state(
                logger=logger,
                log_level=log_level,
                log_fmt=log_fmt,
            ),
            # FastDepends args
            _get_dependant=_get_dependant,
            _call_decorators=_call_decorators,
            apply_types=apply_types,
            serializer=serializer,
        )
        self.client_id = client_id

        self.config = ConfluentFastConfig(config)

        self._state.patch_value(
            producer=AsyncConfluentFastProducer(
                parser=self._parser,
                decoder=self._decoder,
            )
        )

    async def close(
        self,
        exc_type: Optional[type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        await super().close(exc_type, exc_val, exc_tb)

        await self._producer.disconnect()

        self._connection = None

    async def connect(
        self,
        bootstrap_servers: Annotated[
            Union[str, Iterable[str]],
            Doc("Kafka addresses to connect."),
        ] = EMPTY,
        **kwargs: Any,
    ) -> Callable[..., AsyncConfluentConsumer]:
        if bootstrap_servers is not EMPTY:
            kwargs["bootstrap_servers"] = bootstrap_servers

        return await super().connect(**kwargs)

    @override
    async def _connect(  # type: ignore[override]
        self,
        *,
        client_id: str,
        **kwargs: Any,
    ) -> Callable[..., AsyncConfluentConsumer]:
        security_params = parse_security(self.security)
        kwargs.update(security_params)

        native_producer = AsyncConfluentProducer(
            **kwargs,
            client_id=client_id,
            config=self.config,
            logger=self._state.get().logger_state,
        )

        self._producer.connect(native_producer)

        connection_kwargs, _ = filter_by_dict(ConsumerConnectionParams, kwargs)
        return partial(
            AsyncConfluentConsumer,
            **connection_kwargs,
            logger=self._state.get().logger_state,
            config=self.config,
        )

    async def start(self) -> None:
        await self.connect()
        self._setup()
        await super().start()

    @property
    def _subscriber_setup_extra(self) -> "AnyDict":
        return {
            **super()._subscriber_setup_extra,
            "client_id": self.client_id,
            "builder": self._connection,
        }

    @override
    async def publish(  # type: ignore[override]
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ],
        topic: Annotated[
            str,
            Doc("Topic where the message will be published."),
        ],
        *,
        key: Union[bytes, str, None] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Annotated[
            Optional[dict[str, str]],
            Doc("Message headers to store metainformation."),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("Reply message topic name to send response."),
        ] = "",
        no_confirm: Annotated[
            bool,
            Doc("Do not wait for Kafka publish confirmation."),
        ] = False,
    ) -> "asyncio.Future":
        """Publish message directly.

        This method allows you to publish message in not AsyncAPI-documented way. You can use it in another frameworks
        applications or to publish messages from time to time.

        Please, use `@broker.publisher(...)` or `broker.publisher(...).publish(...)` instead in a regular way.
        """
        cmd = KafkaPublishCommand(
            message,
            topic=topic,
            key=key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=headers,
            reply_to=reply_to,
            no_confirm=no_confirm,
            correlation_id=correlation_id or gen_cor_id(),
            _publish_type=PublishType.PUBLISH,
        )
        return await super()._basic_publish(cmd, producer=self._producer)

    @override
    async def request(  # type: ignore[override]
        self,
        message: "SendableMessage",
        topic: str,
        *,
        key: Union[bytes, str, None] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        timeout: float = 0.5,
    ) -> "KafkaMessage":
        cmd = KafkaPublishCommand(
            message,
            topic=topic,
            key=key,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=headers,
            timeout=timeout,
            correlation_id=correlation_id or gen_cor_id(),
            _publish_type=PublishType.REQUEST,
        )

        msg: KafkaMessage = await super()._basic_request(cmd, producer=self._producer)
        return msg

    async def publish_batch(
        self,
        *messages: "SendableMessage",
        topic: str,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[dict[str, str]] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
        no_confirm: bool = False,
    ) -> None:
        cmd = KafkaPublishCommand(
            *messages,
            topic=topic,
            partition=partition,
            timestamp_ms=timestamp_ms,
            headers=headers,
            reply_to=reply_to,
            no_confirm=no_confirm,
            correlation_id=correlation_id or gen_cor_id(),
            _publish_type=PublishType.PUBLISH,
        )

        return await self._basic_publish_batch(cmd, producer=self._producer)

    @override
    async def ping(self, timeout: Optional[float]) -> bool:
        sleep_time = (timeout or 10) / 10

        with anyio.move_on_after(timeout) as cancel_scope:
            if not self._producer:
                return False

            while True:
                if cancel_scope.cancel_called:
                    return False

                if await self._producer.ping(timeout=timeout):
                    return True

                await anyio.sleep(sleep_time)

        return False
