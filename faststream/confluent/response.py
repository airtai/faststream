from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from faststream.broker.response import Response

if TYPE_CHECKING:
    from faststream.types import AnyDict, SendableMessage


class KafkaResponse(Response):
    def __init__(
        self,
        body: "SendableMessage",
        *,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
        timestamp_ms: Optional[int] = None,
        key: Optional[bytes] = None,
    ) -> None:
        super().__init__(
            body=body,
            headers=headers,
            correlation_id=correlation_id,
        )

        self.timestamp_ms = timestamp_ms
        self.key = key

    @override
    def as_publish_kwargs(self) -> "AnyDict":
        publish_options = {
            **super().as_publish_kwargs(),
            "timestamp_ms": self.timestamp_ms,
            "key": self.key,
        }
        return publish_options
