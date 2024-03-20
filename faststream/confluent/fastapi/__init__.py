from typing_extensions import Annotated

from faststream.confluent.fastapi.fastapi import KafkaRouter
from faststream.broker.fastapi.context import Context, ContextRepo, Logger
from faststream.confluent.message import KafkaMessage as KM
from faststream.confluent.producer import AsyncConfluentFastProducer
from faststream.confluent.broker import KafkaBroker as KB

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
KafkaProducer = Annotated[AsyncConfluentFastProducer, Context("broker._producer")]
