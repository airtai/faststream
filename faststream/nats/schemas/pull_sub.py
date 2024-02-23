from typing import Optional

from pydantic import BaseModel, Field


class PullSub(BaseModel):
    """A class to represent a NATS pull subscription."""

    batch_size: int = Field(default=1)
    timeout: Optional[float] = Field(default=5.0)
    batch: bool = Field(default=False)

    def __init__(
        self,
        batch_size: int = 1,
        timeout: Optional[float] = 5.0,
        batch: bool = False,
    ) -> None:
        """Initialize the NATS pull subscription.

        Args:
            batch_size: The batch size.
            timeout: The timeout.
            batch: Whether to batch.
        """
        super().__init__(
            batch_size=batch_size,
            timeout=timeout,
            batch=batch,
        )
