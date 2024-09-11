"""AsyncAPI Kafka bindings.

References: https://github.com/asyncapi/bindings/tree/master/kafka
"""

from typing import Optional

from pydantic import BaseModel, PositiveInt
from typing_extensions import Self

from faststream.specification import schema as spec


class ChannelBinding(BaseModel):
    """A class to represent a channel binding.

    Attributes:
        topic : optional string representing the topic
        partitions : optional positive integer representing the number of partitions
        replicas : optional positive integer representing the number of replicas
        bindingVersion : string representing the binding version
    """

    topic: Optional[str] = None
    partitions: Optional[PositiveInt] = None
    replicas: Optional[PositiveInt] = None
    bindingVersion: str = "0.4.0"

    # TODO:
    # topicConfiguration

    @classmethod
    def from_spec(cls, binding: spec.bindings.kafka.ChannelBinding) -> Self:
        return cls(
            topic=binding.topic,
            partitions=binding.partitions,
            replicas=binding.replicas,
            bindingVersion=binding.bindingVersion,
        )


def from_spec(binding: spec.bindings.kafka.ChannelBinding) -> ChannelBinding:
    return ChannelBinding.from_spec(binding)
