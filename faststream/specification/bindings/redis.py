"""AsyncAPI Redis bindings.

References: https://github.com/asyncapi/bindings/tree/master/redis
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
        channel : the channel name
        method : the method used for binding (ssubscribe, psubscribe, subscribe)
        bindingVersion : the version of the binding
    """

    channel: str
    method: Optional[str] = None
    group_name: Optional[str] = None
    consumer_name: Optional[str] = None
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
