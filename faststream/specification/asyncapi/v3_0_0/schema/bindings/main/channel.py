from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings import ChannelBinding
from faststream.specification.asyncapi.v2_6_0.schema.bindings.main import (
    channel_binding_from_spec,
)
from faststream.specification.asyncapi.v3_0_0.schema.bindings.amqp import (
    channel_binding_from_spec as amqp_channel_binding_from_spec,
)


def from_spec(binding: spec.bindings.ChannelBinding) -> ChannelBinding:
    channel_binding = channel_binding_from_spec(binding)

    if binding.amqp:
        channel_binding.amqp = amqp_channel_binding_from_spec(binding.amqp)

    return channel_binding
