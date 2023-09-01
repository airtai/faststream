from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2, model_to_json, model_to_jsonable
from faststream.asyncapi.schema.channels import Channel
from faststream.asyncapi.schema.info import Info
from faststream.asyncapi.schema.message import Message
from faststream.asyncapi.schema.servers import Server
from faststream.asyncapi.schema.utils import (
    ExternalDocs,
    ExternalDocsDict,
    Tag,
    TagDict,
)

ASYNC_API_VERSION = "2.6.0"


class Components(BaseModel):
    # TODO
    # servers
    # serverVariables
    # channels
    messages: Optional[Dict[str, Message]] = None
    schemas: Optional[Dict[str, Dict[str, Any]]] = None

    # securitySchemes
    # parameters
    # correlationIds
    # operationTraits
    # messageTraits
    # serverBindings
    # channelBindings
    # operationBindings
    # messageBindings

    if PYDANTIC_V2:
        model_config = {"extra": "allow"}

    else:

        class Config:
            extra = "allow"


class Schema(BaseModel):
    asyncapi: str = ASYNC_API_VERSION
    id: Optional[str] = None
    defaultContentType: Optional[str] = None
    info: Info
    servers: Optional[Dict[str, Server]] = None
    channels: Dict[str, Channel]
    components: Optional[Components] = None
    tags: Optional[List[Union[Tag, TagDict, Dict[str, Any]]]] = None
    externalDocs: Optional[Union[ExternalDocs, ExternalDocsDict, Dict[str, Any]]] = None

    def to_jsonable(self) -> Any:
        return model_to_jsonable(
            self,
            by_alias=True,
            exclude_none=True,
        )

    def to_json(self) -> str:
        return model_to_json(
            self,
            by_alias=True,
            exclude_none=True,
        )

    def to_yaml(self) -> str:
        from io import StringIO

        import yaml

        io = StringIO(initial_value="", newline="\n")
        yaml.dump(self.to_jsonable(), io, sort_keys=False)
        return io.getvalue()
