from aiokafka import AIOKafkaConsumer
from typing_extensions import Annotated

from faststream._internal.context import Context
from faststream.annotations import ContextRepo, Logger
from faststream.kafka.broker import KafkaBroker as KB
from faststream.kafka.message import KafkaMessage as KM
from faststream.kafka.publisher.producer import AioKafkaFastProducer
from faststream.params import NoCast

__all__ = (
    "Logger",
    "ContextRepo",
    "NoCast",
    "KafkaMessage",
    "KafkaBroker",
    "KafkaProducer",
)

Consumer = Annotated[AIOKafkaConsumer, Context("handler_.consumer")]
KafkaMessage = Annotated[KM, Context("message")]
KafkaBroker = Annotated[KB, Context("broker")]
KafkaProducer = Annotated[AioKafkaFastProducer, Context("broker._producer")]
