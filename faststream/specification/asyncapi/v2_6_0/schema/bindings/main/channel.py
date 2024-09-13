from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream._internal._compat import PYDANTIC_V2
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings import (
    amqp as amqp_bindings,
)
from faststream.specification.asyncapi.v2_6_0.schema.bindings import (
    kafka as kafka_bindings,
)
from faststream.specification.asyncapi.v2_6_0.schema.bindings import (
    nats as nats_bindings,
)
from faststream.specification.asyncapi.v2_6_0.schema.bindings import (
    redis as redis_bindings,
)
from faststream.specification.asyncapi.v2_6_0.schema.bindings import sqs as sqs_bindings


class ChannelBinding(BaseModel):
    """A class to represent channel bindings.

    Attributes:
        amqp : AMQP channel binding (optional)
        kafka : Kafka channel binding (optional)
        sqs : SQS channel binding (optional)
        nats : NATS channel binding (optional)
        redis : Redis channel binding (optional)

    """

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

    @classmethod
    def from_spec(cls, binding: spec.bindings.ChannelBinding) -> Self:
        return cls(
            amqp=amqp_bindings.channel_binding_from_spec(binding.amqp)
            if binding.amqp is not None
            else None,
            kafka=kafka_bindings.channel_binding_from_spec(binding.kafka)
            if binding.kafka is not None
            else None,
            sqs=sqs_bindings.channel_binding_from_spec(binding.sqs)
            if binding.sqs is not None
            else None,
            nats=nats_bindings.channel_binding_from_spec(binding.nats)
            if binding.nats is not None
            else None,
            redis=redis_bindings.channel_binding_from_spec(binding.redis)
            if binding.redis is not None
            else None,
        )


def from_spec(binding: spec.bindings.ChannelBinding) -> ChannelBinding:
    return ChannelBinding.from_spec(binding)
