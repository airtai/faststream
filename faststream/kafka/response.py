from typing import TYPE_CHECKING, Iterable, Optional

from faststream.broker.response import Response

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware
    from faststream.types import AnyDict, SendableMessage


class KafkaResponse(Response):
    def __init__(
        self,
        message: "SendableMessage",
        *,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        key: Optional[bytes] = None,
        topic: str = "",
        reply_to: str = "",
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> None: ...
