from typing import TYPE_CHECKING, Iterable, Optional

from faststream.broker.response import Response

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware
    from faststream.types import AnyDict, SendableMessage


class NatsResponse(Response):
    def __init__(
        self,
        message: "SendableMessage",
        subject: str = "",
        *,
        headers: Optional["AnyDict"] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
        stream: Optional[str] = None,
        timeout: Optional[float] = None,
        rpc: Optional[bool] = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> None: ...
