from typing import TYPE_CHECKING, Optional

from faststream.broker.response import Response

if TYPE_CHECKING:
    from faststream.rabbit import RabbitQueue
    from faststream.rabbit.types import AioPikaSendableMessage


class RabbitResponse(Response):
    def __init__(
        self,
        body: "AioPikaSendableMessage",
        *,
        correlation_id: Optional[str] = None,
        queue: Optional["RabbitQueue"] = None,
        routing_key: str = "",
        message_id: Optional[str] = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
    ) -> None: ...
