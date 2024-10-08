from typing import TYPE_CHECKING, Dict, Optional

from typing_extensions import override

from faststream.broker.response import Response

if TYPE_CHECKING:
    from faststream.types import AnyDict, SendableMessage


class NatsResponse(Response):
    def __init__(
        self,
        body: "SendableMessage",
        *,
        headers: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        stream: Optional[str] = None,
    ) -> None:
        super().__init__(
            body=body,
            headers=headers,
            correlation_id=correlation_id,
        )
        self.stream = stream

    @override
    def as_publish_kwargs(self) -> "AnyDict":
        publish_options = {
            **super().as_publish_kwargs(),
            "stream": self.stream,
        }
        return publish_options
