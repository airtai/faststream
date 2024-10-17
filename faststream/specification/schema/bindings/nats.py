"""AsyncAPI NATS bindings.

References: https://github.com/asyncapi/bindings/tree/master/nats
"""

from dataclasses import dataclass
from typing import Any, Optional


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

    replyTo: Optional[dict[str, Any]] = None
    bindingVersion: str = "custom"
