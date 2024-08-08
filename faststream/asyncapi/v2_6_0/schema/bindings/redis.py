"""AsyncAPI Redis bindings.

References: https://github.com/asyncapi/bindings/tree/master/redis
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
        channel : the channel name
        method : the method used for binding (ssubscribe, psubscribe, subscribe)
        bindingVersion : the version of the binding
    """

    channel: str
    method: Optional[str] = None
    group_name: Optional[str] = None
    consumer_name: Optional[str] = None
    bindingVersion: str = "custom"


class OperationBinding(BaseModel):
    """A class to represent an operation binding.

    Attributes:
        replyTo : optional dictionary containing reply information
        bindingVersion : version of the binding (default is "custom")
    """

    replyTo: Optional[Dict[str, Any]] = None
    bindingVersion: str = "custom"
