from dataclasses import dataclass
from typing import List, Optional

<<<<<<<< HEAD:faststream/specification/schema/channel.py
from faststream.specification.schema.bindings import ChannelBinding
from faststream.specification.schema.operation import Operation
========
from faststream.specification.bindings import ChannelBinding
from faststream.specification.operation import Operation
>>>>>>>> 3361c325 (mypy satisfied):faststream/specification/channel.py


@dataclass
class Channel:
    """Channel specification.

    Attributes:
        description : optional description of the channel
        servers : optional list of servers associated with the channel
        bindings : optional channel binding
        subscribe : optional operation for subscribing to the channel
        publish : optional operation for publishing to the channel

    """

    description: Optional[str] = None
    servers: Optional[List[str]] = None
    bindings: Optional[ChannelBinding] = None
    subscribe: Optional[Operation] = None
    publish: Optional[Operation] = None
