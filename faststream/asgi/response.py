from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from faststream.asgi.types import Receive, Scope, Send


class AsgiResponse:
    def __init__(
        self,
        body: bytes,
        status_code: int,
        raw_headers: Optional[Dict[bytes, bytes]] = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.raw_headers = raw_headers or {}

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        prefix = "websocket." if (scope["type"] == "websocket") else ""
        await send(
            {
                "type": f"{prefix}http.response.start",
                "status": self.status_code,
                "headers": list(self.raw_headers.items()),
            }
        )
        await send(
            {
                "type": f"{prefix}http.response.body",
                "body": self.body,
            }
        )
