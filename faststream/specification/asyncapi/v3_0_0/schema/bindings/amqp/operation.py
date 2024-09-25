from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings.amqp import (
    OperationBinding,
)


def from_spec(binding: spec.bindings.amqp.OperationBinding) -> OperationBinding:
    return OperationBinding(
        cc=binding.cc,
        ack=binding.ack,
        replyTo=binding.replyTo,
        deliveryMode=binding.deliveryMode,
        mandatory=binding.mandatory,
        priority=binding.priority,
        bindingVersion="0.3.0"
    )
