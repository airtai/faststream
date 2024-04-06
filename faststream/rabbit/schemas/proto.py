from typing import Optional, Protocol

from faststream.rabbit.schemas.exchange import RabbitExchange
from faststream.rabbit.schemas.queue import RabbitQueue


class BaseRMQInformation(Protocol):
    """Base class to store AsyncAPI RMQ bindings."""

    virtual_host: str
    queue: RabbitQueue
    exchange: Optional[RabbitExchange]
    app_id: Optional[str]
