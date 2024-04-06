import asyncio
from ssl import SSLContext
from time import time
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)

from confluent_kafka import Consumer, KafkaError, KafkaException, Message, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from pydantic import BaseModel

from faststream.log import logger
from faststream.utils.functions import call_or_await

_missing = object()


class MsgToSend(BaseModel):
    """A Pydantic model representing a message to be sent to Kafka.

    Attributes:
        timestamp (int): The timestamp of the message.
        key (Optional[Union[str, bytes]]): The key of the message, can be a string or bytes.
        value (Optional[Union[str, bytes]]): The value of the message, can be a string or bytes.
        headers (List[Tuple[str, bytes]]): A list of headers associated with the message.
    """

    timestamp: int
    key: Optional[Union[str, bytes]]
    value: Optional[Union[str, bytes]]
    headers: List[Tuple[str, bytes]]


class BatchBuilder:
    """A helper class to build a batch of messages to send to Kafka."""

    def __init__(self) -> None:
        """Initializes a new BatchBuilder instance."""
        self._builder: List[MsgToSend] = []

    def append(
        self,
        *,
        timestamp: Optional[int] = None,
        key: Optional[Union[str, bytes]] = None,
        value: Optional[Union[str, bytes]] = None,
        headers: Optional[List[Tuple[str, bytes]]] = None,
    ) -> None:
        """Appends a message to the batch with optional timestamp, key, value, and headers."""
        if timestamp is None:
            timestamp = round(time() * 1000)

        if key is None and value is None:
            raise KafkaException(
                KafkaError(40, reason="Both key and value can't be None")
            )

        if headers is None:
            headers = []

        self._builder.append(
            MsgToSend(timestamp=timestamp, key=key, value=value, headers=headers)
        )


class AsyncConfluentProducer:
    """An asynchronous Python Kafka client using the "confluent-kafka" package."""

    def __init__(
        self,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        bootstrap_servers: Union[str, List[str]] = "localhost",
        client_id: Optional[str] = None,
        metadata_max_age_ms: int = 300000,
        request_timeout_ms: int = 40000,
        api_version: str = "auto",
        acks: Any = _missing,
        key_serializer: Optional[Callable[[bytes], bytes]] = None,
        value_serializer: Optional[Callable[[bytes], bytes]] = None,
        compression_type: Optional[str] = None,
        max_batch_size: int = 16384,
        partitioner: str = "consistent_random",
        max_request_size: int = 1048576,
        linger_ms: int = 0,
        send_backoff_ms: int = 100,
        retry_backoff_ms: int = 100,
        security_protocol: str = "PLAINTEXT",
        ssl_context: Optional[SSLContext] = None,
        connections_max_idle_ms: int = 540000,
        enable_idempotence: bool = False,
        transactional_id: Optional[Union[str, int]] = None,
        transaction_timeout_ms: int = 60000,
        sasl_mechanism: Optional[str] = None,
        sasl_plain_password: Optional[str] = None,
        sasl_plain_username: Optional[str] = None,
        sasl_kerberos_service_name: str = "kafka",
        sasl_kerberos_domain_name: Optional[str] = None,
        sasl_oauth_token_provider: Optional[str] = None,
    ) -> None:
        if isinstance(bootstrap_servers, Iterable) and not isinstance(
            bootstrap_servers, str
        ):
            bootstrap_servers = ",".join(bootstrap_servers)

        if compression_type is None:
            compression_type = "none"

        if acks is _missing or acks == "all":
            acks = -1

        self.config = {
            # "topic.metadata.refresh.interval.ms": 1000,
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
            "metadata.max.age.ms": metadata_max_age_ms,
            "request.timeout.ms": request_timeout_ms,
            "acks": acks,
            "compression.type": compression_type,
            "partitioner": partitioner,
            "message.max.bytes": max_request_size,
            "linger.ms": linger_ms,
            "enable.idempotence": enable_idempotence,
            "transactional.id": transactional_id,
            "transaction.timeout.ms": transaction_timeout_ms,
            "retry.backoff.ms": retry_backoff_ms,
            "security.protocol": security_protocol.lower(),
            "connections.max.idle.ms": connections_max_idle_ms,
            "sasl.kerberos.service.name": sasl_kerberos_service_name,
        }
        if sasl_mechanism:
            self.config.update(
                {
                    "sasl.mechanism": sasl_mechanism,
                    "sasl.username": sasl_plain_username,
                    "sasl.password": sasl_plain_password,
                }
            )

        self.producer = Producer(self.config)
        # self.producer.init_transactions()
        self.producer.list_topics()
        self.loop = loop or asyncio.get_event_loop()

    async def stop(self) -> None:
        """Stop the Kafka producer and flush remaining messages."""
        self.producer.flush()

    async def send(
        self,
        topic: str,
        value: Optional[Union[str, bytes]] = None,
        key: Optional[Union[str, bytes]] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[List[Tuple[str, Union[str, bytes]]]] = None,
    ) -> None:
        """Sends a single message to a Kafka topic."""
        kwargs = {
            k: v
            for k, v in {
                "value": value,
                "key": key,
                "partition": partition,
                "headers": headers,
            }.items()
            if v is not None
        }
        if timestamp_ms is not None:
            kwargs["timestamp"] = timestamp_ms
        self.producer.produce(
            topic,
            **kwargs,
        )
        self.producer.poll(0)

    def create_batch(self) -> BatchBuilder:
        """Creates a batch for sending multiple messages.

        Returns:
            BatchBuilder: An instance of BatchBuilder for building message batches.
        """
        return BatchBuilder()

    async def send_batch(
        self, batch: BatchBuilder, topic: str, *, partition: Optional[int]
    ) -> None:
        """Sends a batch of messages to a Kafka topic."""
        tasks = [
            self.send(
                topic=topic,
                partition=partition,
                timestamp_ms=msg.timestamp,
                key=msg.key,
                value=msg.value,
                headers=msg.headers,  # type: ignore[arg-type]
            )
            for msg in batch._builder
        ]
        await asyncio.gather(*tasks)


class TopicPartition(NamedTuple):
    """A named tuple representing a Kafka topic and partition."""

    topic: str
    partition: int


def create_topics(
    topics: List[str],
    config: Dict[str, Optional[Union[str, int, float, bool, Any]]],
) -> None:
    """Creates Kafka topics using the provided configuration."""
    required_config_params = (
        "allow.auto.create.topics",
        "bootstrap.servers",
        "client.id",
        "request.timeout.ms",
        "metadata.max.age.ms",
        "security.protocol",
        "connections.max.idle.ms",
        "sasl.mechanism",
        "sasl.username",
        "sasl.password",
        "sasl.kerberos.service.name",
    )

    admin_client = AdminClient(
        {x: config[x] for x in required_config_params if x in config}
    )

    fs = admin_client.create_topics(
        [NewTopic(topic, num_partitions=1, replication_factor=1) for topic in topics]
    )

    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
        except Exception as e:  # noqa: PERF203
            if "TOPIC_ALREADY_EXISTS" not in str(e):
                logger.warning(f"Failed to create topic {topic}: {e}")
        else:
            logger.info(f"Topic `{topic}` created.")


class AsyncConfluentConsumer:
    """An asynchronous Python Kafka client for consuming messages using the "confluent-kafka" package."""

    def __init__(
        self,
        *topics: str,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        bootstrap_servers: Union[str, List[str]] = "localhost",
        client_id: Optional[str] = "confluent-kafka-consumer",
        group_id: Optional[str] = None,
        group_instance_id: Optional[str] = None,
        key_deserializer: Optional[Callable[[bytes], bytes]] = None,
        value_deserializer: Optional[Callable[[bytes], bytes]] = None,
        fetch_max_wait_ms: int = 500,
        fetch_max_bytes: int = 52428800,
        fetch_min_bytes: int = 1,
        max_partition_fetch_bytes: int = 1 * 1024 * 1024,
        request_timeout_ms: int = 40 * 1000,
        retry_backoff_ms: int = 100,
        auto_offset_reset: str = "latest",
        enable_auto_commit: bool = True,
        auto_commit_interval_ms: int = 5000,
        check_crcs: bool = True,
        metadata_max_age_ms: int = 5 * 60 * 1000,
        partition_assignment_strategy: Union[str, List[Any]] = "roundrobin",
        max_poll_interval_ms: int = 300000,
        rebalance_timeout_ms: Optional[int] = None,
        session_timeout_ms: int = 10000,
        heartbeat_interval_ms: int = 3000,
        consumer_timeout_ms: int = 200,
        max_poll_records: Optional[int] = None,
        ssl_context: Optional[SSLContext] = None,
        security_protocol: str = "PLAINTEXT",
        api_version: str = "auto",
        exclude_internal_topics: bool = True,
        connections_max_idle_ms: int = 540000,
        isolation_level: str = "read_uncommitted",
        sasl_mechanism: Optional[str] = None,
        sasl_plain_password: Optional[str] = None,
        sasl_plain_username: Optional[str] = None,
        sasl_kerberos_service_name: str = "kafka",
        sasl_kerberos_domain_name: Optional[str] = None,
        sasl_oauth_token_provider: Optional[str] = None,
    ) -> None:
        if group_id is None:
            group_id = "confluent-kafka-consumer-group"

        if isinstance(bootstrap_servers, Iterable) and not isinstance(
            bootstrap_servers, str
        ):
            bootstrap_servers = ",".join(bootstrap_servers)

        self.topics = list(topics)

        if not isinstance(partition_assignment_strategy, str):
            partition_assignment_strategy = ",".join(
                [
                    x if isinstance(x, str) else x().name
                    for x in partition_assignment_strategy
                ]
            )
        self.config = {
            "allow.auto.create.topics": True,
            # "topic.metadata.refresh.interval.ms": 1000,
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
            "group.id": group_id,
            "group.instance.id": group_instance_id,
            "fetch.wait.max.ms": fetch_max_wait_ms,
            "fetch.max.bytes": fetch_max_bytes,
            "fetch.min.bytes": fetch_min_bytes,
            "max.partition.fetch.bytes": max_partition_fetch_bytes,
            # "request.timeout.ms": request_timeout_ms,
            "fetch.error.backoff.ms": retry_backoff_ms,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": enable_auto_commit,
            "auto.commit.interval.ms": auto_commit_interval_ms,
            "check.crcs": check_crcs,
            "metadata.max.age.ms": metadata_max_age_ms,
            "partition.assignment.strategy": partition_assignment_strategy,
            "max.poll.interval.ms": max_poll_interval_ms,
            "session.timeout.ms": session_timeout_ms,
            "heartbeat.interval.ms": heartbeat_interval_ms,
            "security.protocol": security_protocol.lower(),
            "connections.max.idle.ms": connections_max_idle_ms,
            "isolation.level": isolation_level,
            "sasl.kerberos.service.name": sasl_kerberos_service_name,
        }
        if sasl_mechanism:
            self.config.update(
                {
                    "sasl.mechanism": sasl_mechanism,
                    "sasl.username": sasl_plain_username,
                    "sasl.password": sasl_plain_password,
                }
            )

        self.loop = loop or asyncio.get_event_loop()

        create_topics(topics=self.topics, config=self.config)
        self.consumer = Consumer(self.config)

    async def start(self) -> None:
        """Starts the Kafka consumer and subscribes to the specified topics."""
        self.consumer.subscribe(self.topics)

    async def commit(self, asynchronous: bool = True) -> None:
        """Commits the offsets of all messages returned by the last poll operation."""
        await call_or_await(self.consumer.commit, asynchronous=asynchronous)

    async def stop(self) -> None:
        """Stops the Kafka consumer and releases all resources."""
        # NOTE: If we don't explicitly call commit and then close the consumer, the confluent consumer gets stuck.
        # We are doing this to avoid the issue.
        enable_auto_commit = self.config["enable.auto.commit"]
        try:
            if enable_auto_commit:
                await self.commit(asynchronous=False)

        except Exception as e:
            # No offset stored issue is not a problem - https://github.com/confluentinc/confluent-kafka-python/issues/295#issuecomment-355907183
            if "No offset stored" in str(e):
                pass
            else:
                raise e

        # Wrap calls to async to make method cancelable by timeout
        await call_or_await(self.consumer.close)

    async def getone(self, timeout_ms: int = 1000) -> Optional[Message]:
        """Consumes a single message from Kafka."""
        msg = await call_or_await(self.consumer.poll, timeout_ms / 1000)
        return check_msg_error(msg)

    async def getmany(
        self,
        timeout_ms: int = 0,
        max_records: Optional[int] = 10,
    ) -> Tuple[Message, ...]:
        """Consumes a batch of messages from Kafka and groups them by topic and partition."""
        raw_messages: List[Optional[Message]] = await call_or_await(
            self.consumer.consume,
            num_messages=max_records or 10,
            timeout=timeout_ms / 1000,
        )

        return tuple(x for x in map(check_msg_error, raw_messages) if x is not None)


def check_msg_error(msg: Optional[Message]) -> Optional[Message]:
    """Checks for errors in the consumed message."""
    if msg is None or msg.error():
        return None

    return msg
