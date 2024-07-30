from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from faststream.types import AnyDict


class Response:
    def __init__(
        self,
        body: "Any",
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

    def as_publish_kwargs(self) -> "AnyDict":
        publish_options = {
            "headers": self.headers,
            "correlation_id": self.correlation_id,
        }
        return publish_options


def ensure_response(response: Union["Response", "Any"]) -> "Response":
    if isinstance(response, Response):
        return response

    return Response(response)
