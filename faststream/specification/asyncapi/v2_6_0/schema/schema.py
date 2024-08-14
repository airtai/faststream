from typing import Any, Dict, List, Optional, Union

from faststream._compat import model_to_json, model_to_jsonable
from faststream.specification.asyncapi.base.schema import BaseSchema
from faststream.specification.asyncapi.v2_6_0.schema.channels import Channel
from faststream.specification.asyncapi.v2_6_0.schema.components import Components
from faststream.specification.asyncapi.v2_6_0.schema.info import Info
from faststream.specification.asyncapi.v2_6_0.schema.servers import Server
from faststream.specification.asyncapi.v2_6_0.schema.utils import (
    ExternalDocs,
    ExternalDocsDict,
    Tag,
    TagDict,
)
from faststream.specification.asyncapi.version import AsyncAPIVersion


class Schema(BaseSchema):
    """A class to represent a schema.

    Attributes:
        asyncapi : version of the async API
        id : optional ID
        defaultContentType : optional default content type
        info : information about the schema
        servers : optional dictionary of servers
        channels : dictionary of channels
        components : optional components of the schema
        tags : optional list of tags
        externalDocs : optional external documentation

    Methods:
        to_jsonable() -> Any: Convert the schema to a JSON-serializable object.
        to_json() -> str: Convert the schema to a JSON string.
        to_yaml() -> str: Convert the schema to a YAML string.

    """

    asyncapi: AsyncAPIVersion = AsyncAPIVersion.v2_6
    id: Optional[str] = None
    defaultContentType: Optional[str] = None
    info: Info
    servers: Optional[Dict[str, Server]] = None
    channels: Dict[str, Channel]
    components: Optional[Components] = None
    tags: Optional[List[Union[Tag, TagDict, Dict[str, Any]]]] = None
    externalDocs: Optional[Union[ExternalDocs, ExternalDocsDict, Dict[str, Any]]] = None

    def to_jsonable(self) -> Any:
        """Convert the schema to a JSON-serializable object."""
        return model_to_jsonable(
            self,
            by_alias=True,
            exclude_none=True,
        )

    def to_json(self) -> str:
        """Convert the schema to a JSON string."""
        return model_to_json(
            self,
            by_alias=True,
            exclude_none=True,
        )

    def to_yaml(self) -> str:
        """Convert the schema to a YAML string."""
        from io import StringIO

        import yaml

        io = StringIO(initial_value="", newline="\n")
        yaml.dump(self.to_jsonable(), io, sort_keys=False)
        return io.getvalue()
