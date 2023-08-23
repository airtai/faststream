from aiokafka import ConsumerRecord

from propan.broker.fastapi.router import PropanRouter
from propan.kafka.broker import KafkaBroker


class KafkaRouter(PropanRouter[ConsumerRecord]):
    broker_class = KafkaBroker
