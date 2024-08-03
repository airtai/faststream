from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
)

from faststream.asgi.handlers import get
from faststream.asgi.response import AsgiResponse
from faststream.asyncapi import get_app_schema, get_asyncapi_html

if TYPE_CHECKING:
    from faststream.asgi.types import ASGIApp, Scope
    from faststream.asyncapi.proto import AsyncAPIApplication
    from faststream.broker.core.usecase import BrokerUsecase


def make_ping_asgi(
    broker: "BrokerUsecase[Any, Any]",
    /,
    timeout: Optional[float] = None,
) -> "ASGIApp":
    healthy_response = AsgiResponse(b"", 204)
    unhealthy_response = AsgiResponse(b"", 500)

    @get
    async def ping(scope: "Scope") -> AsgiResponse:
        if await broker.ping(timeout):
            return healthy_response
        else:
            return unhealthy_response

    return ping


def make_asyncapi_html(app: "AsyncAPIApplication") -> "ASGIApp":
    return AsgiResponse(
        get_asyncapi_html(get_app_schema(app)).encode("utf-8"),
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )
