from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings.amqp import ChannelBinding
from faststream.specification.asyncapi.v2_6_0.schema.bindings.amqp.channel import (
    Exchange,
    Queue,
)


def from_spec(binding: spec.bindings.amqp.ChannelBinding) -> ChannelBinding:
    return ChannelBinding(
        **{
            "is": binding.is_,
            "bindingVersion": "0.3.0",
            "queue": Queue.from_spec(binding.queue)
            if binding.queue is not None and binding.is_ == "queue"
            else None,
            "exchange": Exchange.from_spec(binding.exchange)
            if binding.exchange is not None and binding.is_ == "routingKey"
            else None,
        },
    )
