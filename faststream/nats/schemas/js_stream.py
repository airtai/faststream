from typing import Any, List, Optional

from nats.js.api import (
    DiscardPolicy,
    ExternalStream,
    Placement,
    RePublish,
    RetentionPolicy,
    StorageType,
    StreamConfig,
    StreamSource,
)
from pydantic import Field

from faststream.broker.schemas import NameRequired

__all__ = (
    "JStream",
    # import to prevent Pydantic ForwardRef error
    "RetentionPolicy",
    "DiscardPolicy",
    "StorageType",
    "Placement",
    "StreamSource",
    "ExternalStream",
    "RePublish",
    "Optional",
)


class JStream(NameRequired):
    """A class to represent a JetStream stream."""

    config: StreamConfig

    subjects: List[str] = Field(default_factory=list)
    declare: bool = Field(default=True)

    def __init__(
        self,
        name: str,
        *args: Any,
        declare: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize the JetStream stream.

        Args:
            name: The stream name.
            *args: The arguments.
            declare: Whether to declare the stream.
            **kwargs: The keyword arguments.
        """
        super().__init__(
            name=name,
            declare=declare,
            subjects=[],
            config=StreamConfig(
                *args,
                name=name,
                **kwargs,  # type: ignore[misc]
            ),
        )
