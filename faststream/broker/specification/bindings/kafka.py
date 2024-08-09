"""AsyncAPI Kafka bindings.

References: https://github.com/asyncapi/bindings/tree/master/kafka
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ServerBinding:
    """A class to represent a server binding.

    Attributes:
        bindingVersion : version of the binding (default: "0.4.0")
    """

    bindingVersion: str = "0.4.0"


@dataclass
class ChannelBinding:
    """A class to represent a channel binding.

    Attributes:
        topic : optional string representing the topic
        partitions : optional positive integer representing the number of partitions
        replicas : optional positive integer representing the number of replicas
        bindingVersion : string representing the binding version
    """

    topic: Optional[str] = None
    partitions: Optional[int] = None
    replicas: Optional[int] = None
    bindingVersion: str = "0.4.0"

    # TODO:
    # topicConfiguration


@dataclass
class OperationBinding:
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
