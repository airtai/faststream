from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any, Iterable, Optional, Union

from aio_pika import IncomingMessage
from typing_extensions import override

from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.rabbit.handler import LogicHandler
from faststream.rabbit.schemas.schemas import BaseRMQInformation

if TYPE_CHECKING:
    import aiormq
    from aio_pika.abc import TimeoutType

    from faststream.broker.types import PublisherMiddleware
    from faststream.rabbit.producer import AioPikaFastProducer
    from faststream.rabbit.schemas.schemas import RabbitExchange, RabbitQueue
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.types import AnyDict, SendableMessage


@dataclass
class LogicPublisher(
    BasePublisher[IncomingMessage],
    BaseRMQInformation,
):
    """A class to represent a RabbitMQ publisher."""

    routing_key: str
    mandatory: bool
    immediate: bool
    persist: bool
    timeout: "TimeoutType"
    reply_to: Optional[str]
    app_id: Optional[str]

    priority: Optional[int]
    message_kwargs: "AnyDict"

    _producer: Optional["AioPikaFastProducer"]

    def __init__(
        self,
        *,
        app_id: str,
        routing_key: str,
        mandatory: bool,
        immediate: bool,
        persist: bool,
        virtual_host: str,
        queue: "RabbitQueue",
        exchange: Optional["RabbitExchange"],
        timeout: "TimeoutType",
        reply_to: Optional[str],
        priority: Optional[int],
        message_kwargs: "AnyDict",
        # Regular publisher options
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI options
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        """Initialize NATS publisher object."""
        super().__init__(
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.routing_key = routing_key
        self.mandatory = mandatory
        self.immediate = immediate
        self.timeout = timeout
        self.reply_to = reply_to
        self.priority = priority
        self.message_kwargs = message_kwargs
        self.persist = persist

        self._producer = None

        # BaseRMQInformation
        self.app_id = app_id
        self.queue = queue
        self.exchange = exchange
        self.virtual_host = virtual_host

    @property
    def routing(self) -> Optional[str]:
        return self.routing_key or self.queue.routing

    def _get_routing_hash(self) -> int:
        return LogicHandler.get_routing_hash(self.queue, self.exchange) + hash(
            self.routing_key
        )

    @override
    async def _publish(  # type: ignore[override]
        self,
        message: "AioPikaSendableMessage" = "",
        **publish_kwargs: Any,  # call kwargs merged with publish_kwargs
    ) -> Union["aiormq.abc.ConfirmationFrameType", "SendableMessage"]:
        """Publish a message.

        Args:
            message: The message to be published.
            **publish_kwargs: Additional keyword arguments for the message.

        Returns:
            ConfirmationFrameType or SendableMessage: The result of the publish operation.
        """
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        return await self._producer.publish(
            message=message,
            **(self.message_kwargs | publish_kwargs),
        )

    @cached_property
    def publish_kwargs(self) -> "AnyDict":  # type: ignore[overide]
        return {
            "exchange": self.exchange,
            "routing_key": self.routing,
            "reply_to": self.reply_to,
            "mandatory": self.mandatory,
            "immediate": self.immediate,
            "persist": self.persist,
            "priority": self.priority,
            "timeout": self.timeout,
            "app_id": self.app_id,
        }
