from aiokafka import ConsumerRecord
from typing_extensions import Annotated

from faststream.broker.fastapi.context import Context, ContextRepo, Logger
from faststream.broker.fastapi.router import StreamRouter
from faststream.kafka.broker import KafkaBroker as KB
from faststream.kafka.message import KafkaMessage as KM
from faststream.kafka.producer import AioKafkaFastProducer

__all__ = (
    "Context",
    "Logger",
    "ContextRepo",
    "KafkaRouter",
    "KafkaMessage",
    "KafkaBroker",
    "KafkaProducer",
)

KafkaMessage = Annotated[KM, Context("message")]
KafkaBroker = Annotated[KB, Context("broker")]
KafkaProducer = Annotated[AioKafkaFastProducer, Context("broker._producer")]


class KafkaRouter(StreamRouter[ConsumerRecord]):
    """A class to route Kafka streams.

    Attributes:
        broker_class : class representing the Kafka broker

    Methods:
        _setup_log_context : sets up the log context for the main broker and including broker
    """

    broker_class = KB

    @staticmethod
    def _setup_log_context(
        main_broker: KB,
        including_broker: KB,
    ) -> None:
        """Set up log context for a Kafka broker.

        Args:
            main_broker: The main Kafka broker.
            including_broker: The Kafka broker to include in the log context.

        Returns:
            None
        """
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(h.topics)
