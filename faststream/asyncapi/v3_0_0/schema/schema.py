from typing import Any, Dict, Optional

from faststream._compat import model_to_json, model_to_jsonable
from faststream.asyncapi.schema.schema import BaseSchema
from faststream.asyncapi.v3_0_0.schema.channels import Channel
from faststream.asyncapi.v3_0_0.schema.components import Components
from faststream.asyncapi.v3_0_0.schema.info import Info
from faststream.asyncapi.v3_0_0.schema.operations import Operation
from faststream.asyncapi.v3_0_0.schema.servers import Server
from faststream.asyncapi.version import AsyncAPIVersion


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

    Methods:
        to_jsonable() -> Any: Convert the schema to a JSON-serializable object.
        to_json() -> str: Convert the schema to a JSON string.
        to_yaml() -> str: Convert the schema to a YAML string.

    """

    asyncapi: AsyncAPIVersion = AsyncAPIVersion.v3_0
    id: Optional[str] = None
    defaultContentType: Optional[str] = None
    info: Info
    servers: Optional[Dict[str, Server]] = None
    channels: Dict[str, Channel]
    operations: Dict[str, Operation]
    components: Optional[Components] = None

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
