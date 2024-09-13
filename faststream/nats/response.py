from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from faststream.response import Response

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, SendableMessage


class NatsResponse(Response):
    def __init__(
        self,
        body: "SendableMessage",
        *,
        headers: Optional["AnyDict"] = None,
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
