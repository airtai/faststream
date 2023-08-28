from aiokafka import ConsumerRecord

from faststream.broker.fastapi.router import StreamRouter
from faststream.kafka.broker import KafkaBroker


class KafkaRouter(StreamRouter[ConsumerRecord]):
    broker_class = KafkaBroker
