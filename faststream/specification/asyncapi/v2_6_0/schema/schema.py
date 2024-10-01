from typing import Dict, List, Literal, Optional, Union

from faststream._internal.basic_types import AnyDict
from faststream.specification.asyncapi.v2_6_0.schema.channels import Channel
from faststream.specification.asyncapi.v2_6_0.schema.components import Components
from faststream.specification.asyncapi.v2_6_0.schema.docs import ExternalDocs
from faststream.specification.asyncapi.v2_6_0.schema.info import Info
from faststream.specification.asyncapi.v2_6_0.schema.servers import Server
from faststream.specification.asyncapi.v2_6_0.schema.tag import Tag
from faststream.specification.base.schema import BaseSchema


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
    """

    info: Info

    asyncapi: Union[Literal["2.6.0"], str] = "2.6.0"
    id: Optional[str] = None
    defaultContentType: Optional[str] = None
    servers: Optional[Dict[str, Server]] = None
    channels: Dict[str, Channel]
    components: Optional[Components] = None
    tags: Optional[List[Union[Tag, AnyDict]]] = None
    externalDocs: Optional[Union[ExternalDocs, AnyDict]] = None
