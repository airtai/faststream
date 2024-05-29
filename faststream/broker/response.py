from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from faststream.types import AnyDict, SendableMessage


class Response:
    def __new__(
        cls,
        body: Union[
            "SendableMessage",
            "Response",
        ],
        **kwargs: Any,
    ) -> "Response":
        """Create a new instance of the class."""
        if isinstance(body, cls):
            return body

        else:
            return super().__new__(cls)

    def __init__(
        self,
        body: "SendableMessage",
        *,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Initialize a handler."""
        if not isinstance(body, Response):
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

    def as_publish_kwargs(self) -> "AnyDict":
        publish_options = {
            "headers": self.headers,
            "correlation_id": self.correlation_id,
        }
        return publish_options
