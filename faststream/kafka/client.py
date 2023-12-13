import asyncio
from time import time
from typing import Generic, Iterable, List, Optional, Sequence, Tuple, TypeVar, NamedTuple, Dict

from confluent_kafka import KafkaException, Producer, Consumer
from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from asyncer import asyncify

KT = TypeVar("KT")
VT = TypeVar("VT")

_missing = object()


@dataclass
class ConsumerRecord(Generic[KT, VT]):
    topic: str
    "The topic this record is received from"

    partition: int
    "The partition from which this record is received"

    offset: int
    "The position of this record in the corresponding Kafka partition."

    timestamp: int
    "The timestamp of this record"

    timestamp_type: int
    "The timestamp type of this record"

    key: Optional[KT]
    "The key (or `None` if no key is specified)"

    value: Optional[VT]
    "The value"

    checksum: int
    "Deprecated"

    serialized_key_size: int
    "The size of the serialized, uncompressed key in bytes."

    serialized_value_size: int
    "The size of the serialized, uncompressed value in bytes."

    headers: Sequence[Tuple[str, bytes]]
    "The headers"


class MsgToSend(BaseModel):
    timestamp: int
    key: Optional[str]
    value: Optional[str]
    headers: List[Tuple[str, bytes]]


class BatchBuilder:
    def __init__(self):
        self._builder = []

    def append(
        self,
        *,
        timestamp: Optional[int] = None,
        key: Optional[str] = None,
        value: Optional[str] = None,
        headers: Optional[List[Tuple[str, bytes]]] = None,
    ):
        if timestamp is None:
            timestamp = round(time() * 1000)
        if key is None and value is None:
            raise KafkaException("Both key and value can't be None")
        if headers is None:
            headers = []
        self._builder.append(
            MsgToSend(timestamp=timestamp, key=key, value=value, headers=headers)
        )


class AsyncConfluentProducer:
    """
    An asynchronous Python Kafka client using the "confluent-kafka" package.
    """

    def __init__(
        self,
        *,
        loop=None,
        bootstrap_servers="localhost",
        client_id=None,
        metadata_max_age_ms=300000,
        request_timeout_ms=40000,
        api_version="auto",
        acks=_missing,
        key_serializer=None,
        value_serializer=None,
        compression_type=None,
        max_batch_size=16384,
        partitioner="consistent_random",
        max_request_size=1048576,
        linger_ms=0,
        send_backoff_ms=100,
        retry_backoff_ms=100,
        security_protocol="PLAINTEXT",
        ssl_context=None,
        connections_max_idle_ms=540000,
        enable_idempotence=False,
        transactional_id=None,
        transaction_timeout_ms=60000,
        sasl_mechanism="PLAIN",
        sasl_plain_password=None,
        sasl_plain_username=None,
        sasl_kerberos_service_name="kafka",
        sasl_kerberos_domain_name=None,
        sasl_oauth_token_provider=None,
    ):
        """
        Initialize the AsyncConfluentProducer.

        Args:
            config (dict): Configuration dictionary for the Kafka producer.
        """

        if isinstance(bootstrap_servers, Iterable) and not isinstance(
            bootstrap_servers, str
        ):
            bootstrap_servers = ",".join(bootstrap_servers)

        if compression_type is None:
            compression_type = "none"

        if acks is _missing or acks == "all":
            acks = -1

        self.config = {
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
            "sasl.mechanism": sasl_mechanism,
            "sasl.username": sasl_plain_username,
            "sasl.password": sasl_plain_password,
            "sasl.kerberos.service.name": sasl_kerberos_service_name,
        }
        self.producer = Producer(self.config)
        self.loop = loop or asyncio.get_event_loop()

    async def start(self):
        """
        Start the Kafka producer.
        """
        pass

    async def stop(self):
        """
        Stop the Kafka producer and flush remaining messages.
        """
        self.producer.flush()

    async def send(
        self,
        topic,
        value=None,
        key=None,
        partition=None,
        timestamp_ms=None,
        headers=None,
    ):
        """
        Send a single message to a Kafka topic.

        Args:
            topic (str): Name of the Kafka topic.
            key (str): Key of the message.
            value (str): Value of the message.
        """
        d = locals()
        d.pop("topic")
        d.pop("timestamp_ms")
        d.pop("self")
        kwargs = {k: v for k, v in d.items() if v is not None}
        if timestamp_ms is not None:
            kwargs["timestamp"] = timestamp_ms

        # result = self.loop.create_future()
        # def ack(err, msg):
        #     if err:
        #         self.loop.call_soon_threadsafe(result.set_exception, KafkaException(err))
        #     else:
        #         self.loop.call_soon_threadsafe(result.set_result, msg)
        #         print("At callback")

        self.producer.produce(
            topic,
            # on_delivery=ack,
            **kwargs,
        )
        # return result

    def create_batch(self):
        """
        Create a batch for sending multiple messages.
        """
        return BatchBuilder()

    async def send_batch(self, batch, topic, *, partition):
        """
        Send a batch of messages to a Kafka topic.

        Args:
            batch (asyncio.Queue): A queue containing messages to be sent.
        """
        tasks = [
            self.send(
                topic=topic,
                partition=partition,
                timestamp_ms=msg.timestamp,
                key=msg.key,
                value=msg.value,
                headers=msg.headers,
            )
            for msg in batch._builder
        ]
        await asyncio.gather(*tasks)


class TopicPartition(NamedTuple):
    topic: str
    partition: int


class AsyncConfluentConsumer:
    def __init__(
        self,
        *topics,
        loop=None,
        bootstrap_servers="localhost",
        client_id='confluent-kafka-consumer',
        group_id=None,
        group_instance_id=None,
        key_deserializer=None,
        value_deserializer=None,
        fetch_max_wait_ms=500,
        fetch_max_bytes=52428800,
        fetch_min_bytes=1,
        max_partition_fetch_bytes=1 * 1024 * 1024,
        request_timeout_ms=40 * 1000,
        retry_backoff_ms=100,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        auto_commit_interval_ms=5000,
        check_crcs=True,
        metadata_max_age_ms=5 * 60 * 1000,
        partition_assignment_strategy="roundrobin",
        max_poll_interval_ms=300000,
        rebalance_timeout_ms=None,
        session_timeout_ms=10000,
        heartbeat_interval_ms=3000,
        consumer_timeout_ms=200,
        max_poll_records=None,
        ssl_context=None,
        security_protocol="PLAINTEXT",
        api_version="auto",
        exclude_internal_topics=True,
        connections_max_idle_ms=540000,
        isolation_level="read_uncommitted",
        sasl_mechanism="PLAIN",
        sasl_plain_password=None,
        sasl_plain_username=None,
        sasl_kerberos_service_name="kafka",
        sasl_kerberos_domain_name=None,
        sasl_oauth_token_provider=None,
    ):
        if group_id is None:
            group_id = "confluent-kafka-consumer-group"
        if isinstance(bootstrap_servers, Iterable) and not isinstance(bootstrap_servers, str):
            bootstrap_servers = ",".join(bootstrap_servers)
        self.topics = list(topics)
        if not isinstance(partition_assignment_strategy, str):
            partition_assignment_strategy = ",".join([x().name for x in partition_assignment_strategy])
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
            "group.id": group_id,
            "group.instance.id": group_instance_id,

            "fetch.wait.max.ms": fetch_max_wait_ms,
            "fetch.max.bytes": fetch_max_bytes,
            "fetch.min.bytes": fetch_min_bytes,
            "max.partition.fetch.bytes": max_partition_fetch_bytes,
            "request.timeout.ms": request_timeout_ms,
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

            'security.protocol': security_protocol,
            "connections.max.idle.ms": connections_max_idle_ms,
            "isolation.level": isolation_level,
            'sasl.mechanism': sasl_mechanism,
            'sasl.username': sasl_plain_username,
            'sasl.password': sasl_plain_password,
            "sasl.kerberos.service.name": sasl_kerberos_service_name,
        }
        self.consumer = Consumer(self.config)
        self.loop = loop or asyncio.get_event_loop()

    async def start(self):
        await asyncify(self.consumer.subscribe)(self.topics)

    async def poll(self, timeout_ms=1000) -> Optional[ConsumerRecord]:
        timeout = timeout_ms/1000
        msg = await asyncify(self.consumer.poll)(timeout)
        if msg is None:
            return msg
        serialized_key_size = 0 if msg.key() is None else len(msg.key())
        headers = () if msg.headers() is None else msg.headers()
        timestamp_type, timestamp = msg.timestamp()
        # https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#confluent_kafka.Message.timestamp
        timestamp_type = timestamp_type - 1 
        consumer_record = ConsumerRecord(
            topic=msg.topic(),
            partition=msg.partition(),
            offset=msg.offset(),
            timestamp=timestamp,
            timestamp_type=timestamp_type,
            key=msg.key(),
            value=msg.value(),
            checksum=sum(msg.value()),
            serialized_key_size=serialized_key_size,
            serialized_value_size=len(msg.value()),
            headers=headers,
        )
        return consumer_record

    async def commit(self):
        await asyncify(self.consumer.commit)()

    async def stop(self):
        await asyncify(self.consumer.close)()

    async def getone(self) -> ConsumerRecord:
        while True:
            msg = await self.poll()
            if msg is not None:
                break
        return msg

    async def getmany(self, timeout_ms=0, max_records=10) -> Dict[TopicPartition, List[ConsumerRecord]]:
        messages = {}
        for i in range(max_records):
            print(f"Here at {i}")
            msg = await self.poll(timeout_ms=timeout_ms)
            if msg is None:
                continue
            tp = TopicPartition(topic=msg.topic, partition=msg.partition)
            if tp not in messages:
                messages[tp] = []
            messages[tp].append(msg)
        return messages
