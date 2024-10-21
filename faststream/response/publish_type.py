from enum import Enum


class PublishType(str, Enum):
    Publish = "Publish"
    """Regular `broker/publisher.publish(...)` call."""

    Reply = "Reply"
    """Response to RPC/Reply-To request."""

    Request = "Request"
    """RPC request call."""
