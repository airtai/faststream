"""AsyncAPI Kafka bindings.

References: https://github.com/asyncapi/bindings/tree/master/kafka
"""
import typing_extensions
from typing import Any, Dict, Optional

from pydantic import BaseModel, PositiveInt

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
    def from_spec(cls, binding: spec.bindings.kafka.ChannelBinding) -> typing_extensions.Self:
        return cls(
            topic=binding.topic,
            partitions=binding.partitions,
            replicas=binding.replicas,
            bindingVersion=binding.bindingVersion,
        )


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        groupId : optional dictionary representing the group ID
        clientId : optional dictionary representing the client ID
        replyTo : optional dictionary representing the reply-to
        bindingVersion : version of the binding (default: "0.4.0")
    """

    groupId: Optional[Dict[str, Any]] = None
    clientId: Optional[Dict[str, Any]] = None
    replyTo: Optional[Dict[str, Any]] = None
    bindingVersion: str = "0.4.0"

    @classmethod
    def from_spec(cls, binding: spec.bindings.kafka.OperationBinding) -> typing_extensions.Self:
        return cls(
            groupId=binding.groupId,
            clientId=binding.clientId,
            replyTo=binding.replyTo,
            bindingVersion=binding.bindingVersion,
        )
