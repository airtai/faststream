from functools import wraps
from typing import (
    TYPE_CHECKING,
    Sequence,
    Optional
)

from faststream.asgi.response import AsgiResponse

if TYPE_CHECKING:
    from faststream.asgi.types import ASGIApp, Receive, Scope, Send, UserApp


def get(func: Optional["UserApp"] = None, *, include_in_schema: bool = True) -> "ASGIApp":
    methods = ("GET", "HEAD")

    if func is None:
        def decorator(func: "UserApp") -> "ASGIApp":
            return get(func, include_in_schema=include_in_schema)
        return decorator

    method_now_allowed_response = _get_method_not_allowed_response(methods)
    error_response = AsgiResponse(body=b"Internal Server Error", status_code=500)

    @wraps(func)
    async def asgi_wrapper(
        scope: "Scope",
        receive: "Receive",
        send: "Send",
    ) -> None:
        if scope["method"] not in methods:
            response: ASGIApp = method_now_allowed_response

        else:
            try:
                response = await func(scope)
            except Exception:
                response = error_response

        await response(scope, receive, send)
        return
    
    asgi_wrapper.include_in_schema = include_in_schema

    return asgi_wrapper


def _get_method_not_allowed_response(methods: Sequence[str]) -> AsgiResponse:
    return AsgiResponse(
        body=b"Method Not Allowed",
        status_code=405,
        headers={
            "Allow": ", ".join(methods),
        },
    )
