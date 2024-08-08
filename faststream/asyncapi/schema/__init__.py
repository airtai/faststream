"""AsyncAPI schema related functions."""

from faststream.asyncapi.schema.bindings import (
    ChannelBinding,
    OperationBinding,
    ServerBinding,
)
from faststream.asyncapi.schema.info import (
    BaseInfo,
)
from faststream.asyncapi.schema.schema import (
    BaseSchema,
)
from faststream.asyncapi.v2_6_0.schema.security import SecuritySchemaComponent
from faststream.asyncapi.v2_6_0.schema.utils import (
    ExternalDocs,
    ExternalDocsDict,
    Reference,
    Tag,
    TagDict,
)
from faststream.asyncapi.version import AsyncAPIVersion

__all__ = (
    # main
    "AsyncAPIVersion",
    "BaseSchema",
    # info
    "BaseInfo",
    # servers
    # channels
    # utils
    "Tag",
    "TagDict",
    "ExternalDocs",
    "ExternalDocsDict",
    "Reference",
    # bindings
    "ServerBinding",
    "ChannelBinding",
    "OperationBinding",
    # messages
    # security
    "SecuritySchemaComponent",
)
