from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream._internal._compat import PYDANTIC_V2
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings import (
    kafka as kafka_bindings,
    nats as nats_bindings,
    redis as redis_bindings,
    sqs as sqs_bindings,
)
from faststream.specification.asyncapi.v3_0_0.schema.bindings import (
    amqp as amqp_bindings,
)


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        amqp : AMQP operation binding (optional)
        kafka : Kafka operation binding (optional)
        sqs : SQS operation binding (optional)
        nats : NATS operation binding (optional)
        redis : Redis operation binding (optional)

    """

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

    @classmethod
    def from_spec(cls, binding: spec.bindings.OperationBinding) -> Self:
        return cls(
            amqp=amqp_bindings.operation_binding_from_spec(binding.amqp)
            if binding.amqp is not None
            else None,
            kafka=kafka_bindings.operation_binding_from_spec(binding.kafka)
            if binding.kafka is not None
            else None,
            sqs=sqs_bindings.operation_binding_from_spec(binding.sqs)
            if binding.sqs is not None
            else None,
            nats=nats_bindings.operation_binding_from_spec(binding.nats)
            if binding.nats is not None
            else None,
            redis=redis_bindings.operation_binding_from_spec(binding.redis)
            if binding.redis is not None
            else None,
        )


def from_spec(binding: spec.bindings.OperationBinding) -> OperationBinding:
    return OperationBinding.from_spec(binding)
