from aiokafka import AIOKafkaConsumer
from typing_extensions import Annotated

from faststream.annotations import ContextRepo, Logger, NoCast
from faststream.kafka.broker import KafkaBroker as KB
from faststream.kafka.message import KafkaMessage as KM
from faststream.kafka.publisher.producer import AioKafkaFastProducer
from faststream.utils.context import Context

__all__ = (
    "ContextRepo",
    "KafkaBroker",
    "KafkaMessage",
    "KafkaProducer",
    "Logger",
    "NoCast",
)

Consumer = Annotated[AIOKafkaConsumer, Context("handler_.consumer")]
KafkaMessage = Annotated[KM, Context("message")]
KafkaBroker = Annotated[KB, Context("broker")]
KafkaProducer = Annotated[AioKafkaFastProducer, Context("broker._producer")]
