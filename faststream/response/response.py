from typing import TYPE_CHECKING, Any, Optional

from .publish_type import PublishType

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict


class Response:
    def __init__(
        self,
        body: Any,
        *,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Initialize a handler."""
        self.body = body
        self.headers = headers or {}
        self.correlation_id = correlation_id

    def add_headers(
        self,
        extra_headers: "AnyDict",
        *,
        override: bool = True,
    ) -> None:
        if override:
            self.headers = {**self.headers, **extra_headers}
        else:
            self.headers = {**extra_headers, **self.headers}

    def as_publish_command(self) -> "PublishCommand":
        return PublishCommand(
            body=self.body,
            headers=self.headers,
            correlation_id=self.correlation_id,
            _publish_type=PublishType.Reply,
        )


class PublishCommand(Response):
    def __init__(
        self,
        body: Any,
        *,
        _publish_type: PublishType,
        reply_to: str = "",
        destination: str = "",
        correlation_id: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(
            body,
            headers=headers,
            correlation_id=correlation_id,
        )

        self.destination = destination
        self.reply_to = reply_to

        self.publish_type = _publish_type
