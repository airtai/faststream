from collections.abc import Iterable
from functools import partial
from typing import TYPE_CHECKING, Any, Optional

from faststream._internal.basic_types import SendableMessage
from faststream._internal.publisher.proto import BasePublisherProto
from faststream.kafka.response import KafkaPublishCommand

if TYPE_CHECKING:
    from faststream._internal.basic_types import AsyncFunc
    from faststream._internal.publisher.proto import ProducerProto
    from faststream._internal.types import PublisherMiddleware
    from faststream.response.response import PublishCommand


class KafkaFakePublisher(BasePublisherProto):
    """Publisher Interface implementation to use as RPC or REPLY TO answer publisher."""

    def __init__(
        self,
        producer: "ProducerProto",
        topic: str,
    ) -> None:
        """Initialize an object."""
        self._producer = producer
        self.topic = topic

    async def _publish(
        self,
        cmd: "PublishCommand",
        *,
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> Any:
        """This method should be called in subscriber flow only."""
        cmd = KafkaPublishCommand.from_cmd(cmd)
        cmd.destination = self.topic

        call: AsyncFunc = self._producer.publish
        for m in _extra_middlewares:
            call = partial(m, call)

        return await call(cmd)

    async def publish(
        self,
        message: SendableMessage,
        /,
        *,
        correlation_id: Optional[str] = None,
    ) -> Optional[Any]:
        msg = "You can't use `KafkaFakePublisher` directly."
        raise NotImplementedError(msg)

    async def request(
        self,
        message: "SendableMessage",
        /,
        *,
        correlation_id: Optional[str] = None,
    ) -> Any:
        msg = (
            "`KafkaFakePublisher` can be used only to publish "
            "a response for `reply-to` or `RPC` messages."
        )
        raise NotImplementedError(msg)
