from typing import TYPE_CHECKING, Iterable, Optional

from faststream.broker.response import Response

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware
    from faststream.types import AnyDict, SendableMessage


class RedisResponse(Response):
    def __init__(
        self,
        message: Optional["SendableMessage"] = None,
        *,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
        channel: Optional[str] = None,
        reply_to: str = "",
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> None: ...
