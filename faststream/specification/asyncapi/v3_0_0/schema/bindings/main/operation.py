from typing import Optional

from pydantic import BaseModel
from typing_extensions import Self

from faststream._internal._compat import PYDANTIC_V2
from faststream.specification.asyncapi.v3_0_0.schema.bindings import (
    amqp as amqp_bindings,
    kafka as kafka_bindings,
    nats as nats_bindings,
    redis as redis_bindings,
    sqs as sqs_bindings,
)
from faststream.specification.schema.bindings import OperationBinding as SpecBinding


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
    def from_sub(cls, binding: Optional[SpecBinding]) -> Optional[Self]:
        if binding is None:
            return None

        if binding.amqp and (
            amqp := amqp_bindings.OperationBinding.from_sub(binding.amqp)
        ):
            return cls(amqp=amqp)

        if binding.kafka and (
            kafka := kafka_bindings.OperationBinding.from_sub(binding.kafka)
        ):
            return cls(kafka=kafka)

        if binding.nats and (
            nats := nats_bindings.OperationBinding.from_sub(binding.nats)
        ):
            return cls(nats=nats)

        if binding.redis and (
            redis := redis_bindings.OperationBinding.from_sub(binding.redis)
        ):
            return cls(redis=redis)

        if binding.sqs and (sqs := sqs_bindings.OperationBinding.from_sub(binding.sqs)):
            return cls(sqs=sqs)

        return None

    @classmethod
    def from_pub(cls, binding: Optional[SpecBinding]) -> Optional[Self]:
        if binding is None:
            return None

        if binding.amqp and (
            amqp := amqp_bindings.OperationBinding.from_pub(binding.amqp)
        ):
            return cls(amqp=amqp)

        if binding.kafka and (
            kafka := kafka_bindings.OperationBinding.from_pub(binding.kafka)
        ):
            return cls(kafka=kafka)

        if binding.nats and (
            nats := nats_bindings.OperationBinding.from_pub(binding.nats)
        ):
            return cls(nats=nats)

        if binding.redis and (
            redis := redis_bindings.OperationBinding.from_pub(binding.redis)
        ):
            return cls(redis=redis)

        if binding.sqs and (sqs := sqs_bindings.OperationBinding.from_pub(binding.sqs)):
            return cls(sqs=sqs)

        return None
