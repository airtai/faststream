from dataclasses import dataclass, field
from typing import Any, Optional, Union, TYPE_CHECKING

from typing_extensions import override
from functools import cached_property

from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.rabbit.handler import LogicHandler
from faststream.rabbit.schemas.schemas import BaseRMQInformation


if TYPE_CHECKING:
    import aiormq

    from aio_pika import IncomingMessage

    from faststream.rabbit.producer import AioPikaFastProducer
    from faststream.rabbit.types import AioPikaSendableMessage, TimeoutType
    from faststream.types import SendableMessage, AnyDict


@dataclass
class LogicPublisher(BasePublisher["IncomingMessage"], BaseRMQInformation):
    """A class to publish messages for logic processing.

    Attributes:
        _producer : An optional AioPikaFastProducer object.

    Methods:
        publish : Publishes a message for logic processing.
    """
    routing_key: str = ""
    mandatory: bool = True
    immediate: bool = False
    persist: bool = False
    timeout: "TimeoutType" = None
    reply_to: Optional[str] = None

    priority: Optional[int] = None
    message_kwargs: "AnyDict" = field(default_factory=dict)
    _producer: Optional["AioPikaFastProducer"] = field(default=None, init=False)

    @property
    def routing(self) -> Optional[str]:
        return self.routing_key or self.queue.routing

    def _get_routing_hash(self) -> int:
        return LogicHandler.get_routing_hash(self.queue, self.exchange) + hash(self.routing_key)

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
    def publish_kwargs(self) -> "AnyDict":
        return {
            "exchange": self.exchange,
            "routing_key": self.routing,
            "reply_to": self.reply_to,
            "mandatory": self.mandatory,
            "immediate": self.immediate,
            "persist": self.persist,
            "priority": self.priority,
            "timeout": self.timeout
        }
