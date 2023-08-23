from propan._compat import Annotated
from propan.annotations import ContextRepo, Logger, NoCast
from propan.rabbit.broker import RabbitBroker as RB
from propan.rabbit.message import RabbitMessage as RM
from propan.rabbit.producer import AioPikaPropanProducer
from propan.utils.context import Context

__all__ = (
    "Logger",
    "ContextRepo",
    "NoCast",
    "RabbitMessage",
    "RabbitBroker",
    "RabbitProducer",
)

RabbitMessage = Annotated[RM, Context("message")]
RabbitBroker = Annotated[RB, Context("broker")]
RabbitProducer = Annotated[AioPikaPropanProducer, Context("broker._producer")]
