from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
)

from faststream.asgi.handlers import get
from faststream.asgi.response import AsgiResponse
from faststream.specification.asyncapi import AsyncAPI
from faststream.specification.asyncapi.site import (
    ASYNCAPI_CSS_DEFAULT_URL,
    ASYNCAPI_JS_DEFAULT_URL,
    get_asyncapi_html,
)

if TYPE_CHECKING:
    from faststream._internal.broker.broker import BrokerUsecase
    from faststream.asgi.types import ASGIApp, Scope
    from faststream.specification.proto import SpecApplication


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


def make_asyncapi_asgi(
    app: "SpecApplication",
    sidebar: bool = True,
    info: bool = True,
    servers: bool = True,
    operations: bool = True,
    messages: bool = True,
    schemas: bool = True,
    errors: bool = True,
    expand_message_examples: bool = True,
    title: str = "FastStream",
    asyncapi_js_url: str = ASYNCAPI_JS_DEFAULT_URL,
    asyncapi_css_url: str = ASYNCAPI_CSS_DEFAULT_URL,
) -> "ASGIApp":
    if app.broker is None:
        raise RuntimeError()

    return AsgiResponse(
        get_asyncapi_html(
            AsyncAPI(app.broker, schema_version="2.6.0").schema(),
            sidebar=sidebar,
            info=info,
            servers=servers,
            operations=operations,
            messages=messages,
            schemas=schemas,
            errors=errors,
            expand_message_examples=expand_message_examples,
            title=title,
            asyncapi_js_url=asyncapi_js_url,
            asyncapi_css_url=asyncapi_css_url,
        ).encode("utf-8"),
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )
