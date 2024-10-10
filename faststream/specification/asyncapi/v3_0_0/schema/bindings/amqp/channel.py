from faststream.specification.asyncapi.v2_6_0.schema.bindings.amqp import ChannelBinding
from faststream.specification.asyncapi.v2_6_0.schema.bindings.amqp.channel import (
    Exchange,
    Queue,
)
from faststream.specification.schema.bindings import amqp


def from_spec(binding: amqp.ChannelBinding) -> ChannelBinding:
    return ChannelBinding(
        **{
            "is": binding.is_,
            "bindingVersion": "0.3.0",
            "queue": Queue.from_spec(binding.queue)
            if binding.queue is not None
            else None,
            "exchange": Exchange.from_spec(binding.exchange)
            if binding.exchange is not None
            else None,
        },
    )
