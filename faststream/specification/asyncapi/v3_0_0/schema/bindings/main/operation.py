from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema.bindings import OperationBinding
from faststream.specification.asyncapi.v2_6_0.schema.bindings.main import (
    operation_binding_from_spec,
)
from faststream.specification.asyncapi.v3_0_0.schema.bindings.amqp import (
    operation_binding_from_spec as amqp_operation_binding_from_spec,
)


def from_spec(binding: spec.bindings.OperationBinding) -> OperationBinding:
    operation_binding = operation_binding_from_spec(binding)

    if binding.amqp:
        operation_binding.amqp = amqp_operation_binding_from_spec(binding.amqp)

    return operation_binding
