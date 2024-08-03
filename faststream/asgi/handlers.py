from typing import TYPE_CHECKING, Any, Optional

from faststream.asgi.response import AsgiResponse

if TYPE_CHECKING:
    from faststream.asgi.types import ASGIApp, Receive, Scope, Send
    from faststream.broker.core.usecase import BrokerUsecase


def make_ping_asgi(
    broker: "BrokerUsecase[Any, Any]",
    /,
    timeout: Optional[float] = None,
) -> "ASGIApp":
    async def ping(
        scope: "Scope",
        receive: "Receive",
        send: "Send",
    ) -> None:
        if await broker.ping(timeout):
            response = AsgiResponse(b"", status_code=204)
        else:
            response = AsgiResponse(b"", status_code=500)
        await response(scope, receive, send)

    return ping
