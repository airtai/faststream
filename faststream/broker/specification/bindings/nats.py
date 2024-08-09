"""AsyncAPI NATS bindings.

References: https://github.com/asyncapi/bindings/tree/master/nats
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ServerBinding:
    """A class to represent a server binding.

    Attributes:
        bindingVersion : version of the binding (default: "custom")
    """

    bindingVersion: str = "custom"


@dataclass
class ChannelBinding:
    """A class to represent channel binding.

    Attributes:
        subject : subject of the channel binding
        queue : optional queue for the channel binding
        bindingVersion : version of the channel binding, default is "custom"
    """

    subject: str
    queue: Optional[str] = None
    bindingVersion: str = "custom"


@dataclass
class OperationBinding:
    """A class to represent an operation binding.

    Attributes:
        replyTo : optional dictionary containing reply information
        bindingVersion : version of the binding (default is "custom")
    """

    replyTo: Optional[Dict[str, Any]] = None
    bindingVersion: str = "custom"
