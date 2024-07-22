from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

<<<<<<< HEAD:faststream/specification/schema/schema.py
from faststream._compat import model_to_json, model_to_jsonable
from faststream.specification.schema.channel import Channel
from faststream.specification.schema.components import Components
from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
from faststream.specification.schema.info import Info
from faststream.specification.schema.servers import Server
from faststream.specification.schema.tag import Tag
=======
from faststream._compat import PYDANTIC_V2, model_to_json, model_to_jsonable
from faststream.asyncapi.schema.channels import Channel
from faststream.asyncapi.schema.info import BaseInfo, InfoV2_6, InfoV3_0
from faststream.asyncapi.schema.message import Message
from faststream.asyncapi.schema.servers import Server
from faststream.asyncapi.schema.utils import (
    ExternalDocs,
    ExternalDocsDict,
    Tag,
    TagDict,
)
from faststream.asyncapi.version import AsyncAPIVersion

ASYNC_API_VERSION = "2.6.0"


class Components(BaseModel):
    # TODO
    # servers
    # serverVariables
    # channels
    """A class to represent components in a system.

    Attributes:
        messages : Optional dictionary of messages
        schemas : Optional dictionary of schemas

    Note:
        The following attributes are not implemented yet:
        - servers
        - serverVariables
        - channels
        - securitySchemes
        - parameters
        - correlationIds
        - operationTraits
        - messageTraits
        - serverBindings
        - channelBindings
        - operationBindings
        - messageBindings

    """

    messages: Optional[Dict[str, Message]] = None
    schemas: Optional[Dict[str, Dict[str, Any]]] = None
    securitySchemes: Optional[Dict[str, Dict[str, Any]]] = None
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
>>>>>>> e2a839fc (Schema v3 and info v3):faststream/asyncapi/schema/main.py


class BaseSchema(BaseModel):
    """A class to represent a schema.

    Attributes:
        info : information about the schema

    Methods:
        to_jsonable() -> Any: Convert the schema to a JSON-serializable object.
        to_json() -> str: Convert the schema to a JSON string.
        to_yaml() -> str: Convert the schema to a YAML string.

    """

    info: BaseInfo

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


class SchemaV2_6(BaseSchema):  # noqa: N801
    """A class to represent a schema.

    Attributes:
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

<<<<<<< HEAD:faststream/specification/schema/schema.py
=======
    asyncapi: AsyncAPIVersion = AsyncAPIVersion.v2_6
>>>>>>> e2a839fc (Schema v3 and info v3):faststream/asyncapi/schema/main.py
    id: Optional[str] = None
    defaultContentType: Optional[str] = None
    info: InfoV2_6
    servers: Optional[Dict[str, Server]] = None
    channels: Dict[str, Channel]
    components: Optional[Components] = None
    tags: Optional[List[Union[Tag, Dict[str, Any]]]] = None
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


class SchemaV3_0(BaseSchema):  # noqa: N801
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
    info: InfoV3_0
    servers: Optional[Dict[str, Server]] = None
    channels: Dict[str, Channel]
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
