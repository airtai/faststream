from typing import Dict, Literal, Optional, Union

from faststream.specification.asyncapi.base.schema import BaseSchema
from faststream.specification.asyncapi.v3_0_0.schema.channels import Channel
from faststream.specification.asyncapi.v3_0_0.schema.components import Components
from faststream.specification.asyncapi.v3_0_0.schema.info import Info
from faststream.specification.asyncapi.v3_0_0.schema.operations import Operation
from faststream.specification.asyncapi.v3_0_0.schema.servers import Server


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

    asyncapi: Union[Literal["3.0.0"], str] = "3.0.0"
    id: Optional[str] = None
    defaultContentType: Optional[str] = None
    info: Info
    servers: Optional[Dict[str, Server]] = None
    channels: Dict[str, Channel]
    operations: Dict[str, Operation]
    components: Optional[Components] = None
