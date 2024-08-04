from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from faststream.broker.response import Response

if TYPE_CHECKING:
    from faststream.types import AnyDict, SendableMessage


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
        publish_options = {
            **super().as_publish_kwargs(),
            "maxlen": self.maxlen,
        }
        return publish_options
