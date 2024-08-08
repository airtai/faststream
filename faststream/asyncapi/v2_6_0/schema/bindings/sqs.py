"""AsyncAPI SQS bindings.

References: https://github.com/asyncapi/bindings/tree/master/sqs
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class ServerBinding(BaseModel):
    """A class to represent a server binding.

    Attributes:
        bindingVersion : version of the binding (default: "custom")
    """

    bindingVersion: str = "custom"


class ChannelBinding(BaseModel):
    """A class to represent channel binding.

    Attributes:
        queue : a dictionary representing the queue
        bindingVersion : a string representing the binding version (default: "custom")
    """

    queue: Dict[str, Any]
    bindingVersion: str = "custom"


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        replyTo : optional dictionary containing reply information
        bindingVersion : version of the binding, default is "custom"
    """

    replyTo: Optional[Dict[str, Any]] = None
    bindingVersion: str = "custom"
