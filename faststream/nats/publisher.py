from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, Optional, Union

from nats.aio.msg import Msg
from typing_extensions import override

from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.nats.producer import NatsFastProducer, NatsJSFastProducer
from faststream.nats.schemas import JStream
from faststream.types import AnyDict, DecodedMessage, SendableMessage


@dataclass
class LogicPublisher(BasePublisher[Msg]):
    """A class to represent a NATS publisher."""

    subject: str = field(default="")
    reply_to: str = field(default="")
    headers: Optional[Dict[str, str]] = field(default=None)
    stream: Optional[JStream] = field(default=None)
    timeout: Optional[float] = field(default=None)

    _producer: Union[NatsFastProducer, NatsJSFastProducer, None] = field(
        default=None, init=False
    )

    @override
    async def _publish(  # type: ignore[override]
        self,
        message: SendableMessage = "",
        **producer_kwargs: Any,
    ) -> Optional[DecodedMessage]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101
        assert self.subject, "You have to specify outgoing subject"  # nosec B101

        return await self._producer.publish(
            message=message,
            **producer_kwargs,
        )

    @cached_property
    def publish_kwargs(self) -> AnyDict:
        return {
            "subject": self.subject,
            "reply_to": self.reply_to,
            "headers": self.headers,
        } | (
            {
                "stream": self.stream.name,
                "timeout": self.timeout,
            }
            if self.stream is not None
            else {}
        )
