import asyncio
from time import time
from typing import Generic, Iterable, List, Optional, Sequence, Tuple, TypeVar

from confluent_kafka import KafkaException, Producer
from pydantic import BaseModel
from pydantic.dataclasses import dataclass

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

        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
            "metadata.max.age.ms": metadata_max_age_ms,
            "request.timeout.ms": request_timeout_ms,
            "compression.type": compression_type,
            "partitioner": partitioner,
            "message.max.bytes": max_request_size,
            "linger.ms": linger_ms,
            "enable.idempotence": enable_idempotence,
            "transactional.id": transactional_id,
            "transaction.timeout.ms": transaction_timeout_ms,
            "fetch.error.backoff.ms": retry_backoff_ms,
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
