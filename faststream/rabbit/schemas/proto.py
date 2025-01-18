from typing import TYPE_CHECKING, Any, Optional

from faststream.rabbit.schemas.base import RabbitBaseOptions

if TYPE_CHECKING:
    from faststream.rabbit.schemas.exchange import RabbitExchange
    from faststream.rabbit.schemas.queue import RabbitQueue


class BaseRMQInformation:
    """Base class to store Specification RMQ bindings."""

    virtual_host: str
    queue: "RabbitQueue"
    exchange: "RabbitExchange"
    app_id: Optional[str]

    def __init__(self, *, rabbit_mq_options: RabbitBaseOptions) -> None:
        self.queue = rabbit_mq_options.queue
        self.exchange = rabbit_mq_options.exchange

        # Setup it later
        self.app_id = None
        self.virtual_host = ""

    def _setup(
        self,
        *,
        app_id: Optional[str],
        virtual_host: str,
        **kwargs: Any,
    ) -> None:
        self.app_id = app_id
        self.virtual_host = virtual_host

        # Setup next parent class
        super()._setup(**kwargs)  # type: ignore[misc]
