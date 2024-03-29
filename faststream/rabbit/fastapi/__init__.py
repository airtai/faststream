from typing_extensions import Annotated

from faststream.broker.fastapi.context import Context, ContextRepo, Logger
from faststream.rabbit.broker import RabbitBroker as RB
from faststream.rabbit.fastapi.router import RabbitRouter
from faststream.rabbit.message import RabbitMessage as RM
from faststream.rabbit.publisher.producer import AioPikaFastProducer

RabbitMessage = Annotated[RM, Context("message")]
RabbitBroker = Annotated[RB, Context("broker")]
RabbitProducer = Annotated[AioPikaFastProducer, Context("broker._producer")]

__all__ = (
    "Context",
    "Logger",
    "ContextRepo",
    "RabbitMessage",
    "RabbitBroker",
    "RabbitProducer",
    "RabbitRouter",
)
