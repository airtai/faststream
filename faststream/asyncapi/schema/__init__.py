"""AsyncAPI schema related functions."""

from faststream.asyncapi.schema.bindings import (
    ChannelBinding,
    OperationBinding,
    ServerBinding,
)
from faststream.asyncapi.schema.channels import Channel
from faststream.asyncapi.schema.info import (
    Contact,
    ContactDict,
    Info,
    License,
    LicenseDict,
)
from faststream.asyncapi.schema.main import ASYNC_API_VERSION, Components, Schema
from faststream.asyncapi.schema.message import CorrelationId, Message
from faststream.asyncapi.schema.operations import Operation
from faststream.asyncapi.schema.security import SecuritySchemaComponent
from faststream.asyncapi.schema.servers import Server
from faststream.asyncapi.schema.utils import (
    ExternalDocs,
    ExternalDocsDict,
    Reference,
    Tag,
    TagDict,
)

__all__ = (
    # main
    "ASYNC_API_VERSION",
    "Schema",
    "Components",
    # info
    "Info",
    "Contact",
    "ContactDict",
    "License",
    "LicenseDict",
    # servers
    "Server",
    # channels
    "Channel",
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
    "Message",
    "CorrelationId",
    # security
    "SecuritySchemaComponent",
    # subscription
    "Operation",
)
