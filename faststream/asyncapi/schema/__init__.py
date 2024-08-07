"""AsyncAPI schema related functions."""

from faststream.asyncapi.schema.bindings import (
    ChannelBinding,
    OperationBinding,
    ServerBinding,
)
from faststream.asyncapi.schema.info import (
    BaseInfo,
    Contact,
    ContactDict,
    License,
    LicenseDict,
)
from faststream.asyncapi.schema.message import CorrelationId, Message
from faststream.asyncapi.schema.schema import (
    BaseSchema,
)
from faststream.asyncapi.schema.security import SecuritySchemaComponent
from faststream.asyncapi.schema.utils import (
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
    "Contact",
    "ContactDict",
    "License",
    "LicenseDict",
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
    "CorrelationId",
    "Message",
    # security
    "SecuritySchemaComponent",
)
