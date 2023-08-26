from typing import Optional

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.asyncapi.schema.bindings import amqp as amqp_bindings
from faststream.asyncapi.schema.bindings import kafka as kafka_bindings
from faststream.asyncapi.schema.bindings import nats as nats_bindings
from faststream.asyncapi.schema.bindings import redis as redis_bindings
from faststream.asyncapi.schema.bindings import sqs as sqs_bindings


class ServerBinding(BaseModel):
    amqp: Optional[amqp_bindings.ServerBinding] = None
    kafka: Optional[kafka_bindings.ServerBinding] = None
    sqs: Optional[sqs_bindings.ServerBinding] = None
    nats: Optional[nats_bindings.ServerBinding] = None
    redis: Optional[redis_bindings.ServerBinding] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class ChannelBinding(BaseModel):
    amqp: Optional[amqp_bindings.ChannelBinding] = None
    kafka: Optional[kafka_bindings.ChannelBinding] = None
    sqs: Optional[sqs_bindings.ChannelBinding] = None
    nats: Optional[nats_bindings.ChannelBinding] = None
    redis: Optional[redis_bindings.ChannelBinding] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class OperationBinding(BaseModel):
    amqp: Optional[amqp_bindings.OperationBinding] = None
    kafka: Optional[kafka_bindings.OperationBinding] = None
    sqs: Optional[sqs_bindings.OperationBinding] = None
    nats: Optional[nats_bindings.OperationBinding] = None
    redis: Optional[redis_bindings.OperationBinding] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
