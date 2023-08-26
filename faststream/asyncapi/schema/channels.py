from typing import List, Optional

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.asyncapi.schema.bindings import ChannelBinding
from faststream.asyncapi.schema.operations import Operation
from faststream.asyncapi.schema.utils import Parameter


class Channel(BaseModel):
    description: Optional[str] = None
    servers: Optional[List[str]] = None
    bindings: Optional[ChannelBinding] = None
    subscribe: Optional[Operation] = None
    publish: Optional[Operation] = None
    parameters: Optional[Parameter] = None

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"
