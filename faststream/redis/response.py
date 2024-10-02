from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from faststream.response import Response

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, SendableMessage


class RedisResponse(Response):
    def __init__(
        self,
        body: Optional["SendableMessage"] = None,
        *,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
        maxlen: Optional[int] = None,
    ) -> None:
        super().__init__(
            body=body,
            headers=headers,
            correlation_id=correlation_id,
        )
        self.maxlen = maxlen

    @override
    def as_publish_kwargs(self) -> "AnyDict":
        return {
            **super().as_publish_kwargs(),
            "maxlen": self.maxlen,
        }
