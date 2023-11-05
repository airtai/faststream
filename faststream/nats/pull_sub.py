from typing import Optional

from pydantic import BaseModel, Field


class PullSub(BaseModel):
    batch_size: int = Field(default=1)
    timeout: Optional[float] = Field(default=5.0)

    def __init__(
        self,
        batch_size: int = 1,
        timeout: Optional[float] = 5.0,
    ) -> None:
        super().__init__(
            batch_size=batch_size,
            timeout=timeout,
        )
