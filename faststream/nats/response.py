from typing import TYPE_CHECKING, Optional

from faststream.broker.response import Response

if TYPE_CHECKING:
    from faststream.types import AnyDict, SendableMessage


class NatsResponse(Response):
    def __init__(
        self,
        body: "SendableMessage",
        *,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
        timeout: Optional[float] = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> None: ...
