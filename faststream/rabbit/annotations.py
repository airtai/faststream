from faststream._compat import Annotated
from faststream.annotations import ContextRepo, Logger, NoCast
from faststream.rabbit.broker import RabbitBroker as RB
from faststream.rabbit.message import RabbitMessage as RM
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.utils.context import Context

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
RabbitProducer = Annotated[AioPikaFastProducer, Context("broker._producer")]
