from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from faststream.broker.response import Response

if TYPE_CHECKING:
    from faststream.types import AnyDict, SendableMessage


class NatsResponse(Response):
    def __init__(
        self,
        body: "SendableMessage",
        *,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            body=body,
            headers=headers,
            correlation_id=correlation_id,
        )

    @override
    def as_publish_kwargs(self) -> "AnyDict":
        publish_options = {
            "headers": self.headers,
            "correlation_id": self.correlation_id,
        }
        return publish_options
