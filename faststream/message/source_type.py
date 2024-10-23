from enum import Enum


class SourceType(str, Enum):
    Consume = "Consume"
    """Message consumed by basic subscriber flow."""

    Response = "Response"
    """RPC response consumed."""
