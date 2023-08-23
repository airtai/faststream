from propan._compat import Annotated
from propan.annotations import ContextRepo, Logger, NoCast
from propan.kafka.broker import KafkaBroker as KB
from propan.kafka.message import KafkaMessage as KM
from propan.kafka.producer import AioKafkaPropanProducer
from propan.utils.context import Context

__all__ = (
    "Logger",
    "ContextRepo",
    "NoCast",
    "KafkaMessage",
    "KafkaBroker",
    "KafkaProducer",
)

KafkaMessage = Annotated[KM, Context("message")]
KafkaBroker = Annotated[KB, Context("broker")]
KafkaProducer = Annotated[AioKafkaPropanProducer, Context("broker._producer")]
