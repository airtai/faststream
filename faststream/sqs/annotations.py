from faststream._compat import Annotated
from faststream.annotations import ContextRepo, Logger, NoCast
from faststream.sqs.broker import SQSBroker as SB  # NOQA
from faststream.sqs.message import SQSMessage as SM  # NOQA
from faststream.sqs.producer import SQSFastProducer
from faststream.utils.context import Context

__all__ = (
    "Logger",
    "ContextRepo",
    "NoCast",
    "SQSBroker",
    "SQSMessage",
    "SQSProducer",
)

SQSBroker = Annotated[SB, Context("broker")]
SQSMessage = Annotated[SM, Context("message")]
SQSProducer = Annotated[SQSFastProducer, Context("broker._producer")]
