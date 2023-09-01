from aiokafka import ConsumerRecord

from faststream.broker.fastapi.router import StreamRouter
from faststream.kafka.broker import KafkaBroker


class KafkaRouter(StreamRouter[ConsumerRecord]):
    broker_class = KafkaBroker

    @staticmethod
    def _setup_log_context(
        main_broker: KafkaBroker,
        including_broker: KafkaBroker,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(h.topics)
