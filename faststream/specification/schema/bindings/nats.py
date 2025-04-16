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
    """

    subject: str
    queue: Optional[str]


@dataclass
class OperationBinding:
    """A class to represent an operation binding.

    Attributes:
        reply_to : optional dictionary containing reply information
    """

    reply_to: Optional[dict[str, Any]]
