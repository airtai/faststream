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

from aiokafka import ConsumerRecord
from asyncer import asyncify
from confluent_kafka import Consumer, KafkaException, Message, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from pydantic import BaseModel

_missing = object()


class MsgToSend(BaseModel):
    timestamp: int
    key: Optional[Union[str, bytes]]
    value: Optional[Union[str, bytes]]
    headers: List[Tuple[str, bytes]]


class BatchBuilder:
    def __init__(self) -> None:
        self._builder: List[MsgToSend] = []

    def append(
        self,
        *,
        timestamp: Optional[int] = None,
        key: Optional[Union[str, bytes]] = None,
        value: Optional[Union[str, bytes]] = None,
        headers: Optional[List[Tuple[str, bytes]]] = None,
    ) -> None:
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
        sasl_mechanism: str = "PLAIN",
        sasl_plain_password: Optional[str] = None,
        sasl_plain_username: Optional[str] = None,
        sasl_kerberos_service_name: str = "kafka",
        sasl_kerberos_domain_name: Optional[str] = None,
        sasl_oauth_token_provider: Optional[str] = None,
    ) -> None:
        """
        Initialize the AsyncConfluentProducer.
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
            "sasl.mechanism": sasl_mechanism,
            "sasl.username": sasl_plain_username,
            "sasl.password": sasl_plain_password,
            "sasl.kerberos.service.name": sasl_kerberos_service_name,
        }
        self.producer = Producer(self.config)
        # self.producer.init_transactions()
        self.producer.list_topics()
        self.loop = loop or asyncio.get_event_loop()

    async def start(self) -> None:
        """
        Start the Kafka producer.
        """
        pass

    async def stop(self) -> None:
        """
        Stop the Kafka producer and flush remaining messages.
        """
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
        """
        Send a single message to a Kafka topic.
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
        #     print("At msg on_delivery callback")
        #     if err:
        #         print("Error at ack")
        #         self.loop.call_soon_threadsafe(result.set_exception, KafkaException(err))
        #     else:
        #         print("All good at ack")
        #         self.loop.call_soon_threadsafe(result.set_result, msg)

        self.producer.produce(
            topic,
            # on_delivery=ack,
            **kwargs,
        )
        # return result

    def create_batch(self) -> BatchBuilder:
        """
        Create a batch for sending multiple messages.
        """
        return BatchBuilder()

    async def send_batch(
        self, batch: BatchBuilder, topic: str, *, partition: Optional[int]
    ) -> None:
        """
        Send a batch of messages to a Kafka topic.
        """
        # print("Sending batch messages")
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
        # print("Batch messages sent")


class TopicPartition(NamedTuple):
    topic: str
    partition: int


def create_topics(
    topics: List[str], config: Dict[str, Optional[Union[str, int, float, bool, Any]]]
) -> None:
    print("Creating AdminClient to create topics")
    admin_client = AdminClient(config)
    fs = admin_client.create_topics(
        [NewTopic(topic, num_partitions=1, replication_factor=1) for topic in topics]
    )

    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print(f"Topic {topic} created at create_topics")
        except Exception as e:
            print(f"Failed to create topic {topic}: {e}")


class AsyncConfluentConsumer:
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
        sasl_mechanism: str = "PLAIN",
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
                [x().name for x in partition_assignment_strategy]
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
            "security.protocol": security_protocol,
            "connections.max.idle.ms": connections_max_idle_ms,
            "isolation.level": isolation_level,
            "sasl.mechanism": sasl_mechanism,
            "sasl.username": sasl_plain_username,
            "sasl.password": sasl_plain_password,
            "sasl.kerberos.service.name": sasl_kerberos_service_name,
        }

        self.loop = loop or asyncio.get_event_loop()

        create_topics(topics=self.topics, config=self.config)
        self.consumer = Consumer(self.config)

    async def start(self) -> None:
        # create_topics(topics=self.topics, config=self.config)
        # await asyncify(create_topics)(topics=self.topics, config=self.config)
        await asyncify(self.consumer.subscribe)(self.topics)

    async def convert_to_consumer_record(self, msg: Message) -> ConsumerRecord:
        if msg is None:
            return msg
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            return None
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

    async def poll(self, timeout_ms: int = 1000) -> Optional[ConsumerRecord]:
        timeout = timeout_ms / 1000
        msg = await asyncify(self.consumer.poll)(timeout)
        return await self.convert_to_consumer_record(msg)

    async def consume(
        self, timeout_ms: int = 1000, max_records: int = 1
    ) -> List[ConsumerRecord]:
        timeout = timeout_ms / 1000
        messages = await asyncify(self.consumer.consume)(
            num_messages=max_records, timeout=timeout
        )
        tasks = [self.convert_to_consumer_record(msg) for msg in messages]
        consumer_records = await asyncio.gather(*tasks)
        return [record for record in consumer_records if record is not None]

    async def commit(self) -> None:
        await asyncify(self.consumer.commit)()

    async def stop(self) -> None:
        await asyncify(self.consumer.close)()

    async def getone(self) -> ConsumerRecord:
        while True:
            # msg = await self.poll()
            # if msg is not None:
            #     break
            consumer_records = await self.consume(max_records=1)
            if consumer_records:
                break
        return consumer_records[0]

    async def getmany(
        self, timeout_ms: int = 0, max_records: Optional[int] = 10
    ) -> Dict[TopicPartition, List[ConsumerRecord]]:
        # print("at getmany")

        if max_records is None:
            max_records = 10
        messages: Dict[TopicPartition, List[ConsumerRecord]] = {}
        # for i in range(max_records):
        #     msg = await self.poll(timeout_ms=timeout_ms)
        #     print(f"Here at {i} - {msg}")
        #     if msg is None:
        #         continue
        #     tp = TopicPartition(topic=msg.topic, partition=msg.partition)
        #     if tp not in messages:
        #         messages[tp] = []
        #     messages[tp].append(msg)
        consumer_records = await self.consume(
            max_records=max_records, timeout_ms=timeout_ms
        )
        # print(f"{consumer_records=}")
        for record in consumer_records:
            tp = TopicPartition(topic=record.topic, partition=record.partition)
            if tp not in messages:
                messages[tp] = []
            messages[tp].append(record)
        return messages
