from collections.abc import Iterable
from functools import partial
from typing import TYPE_CHECKING, Any, Optional

from faststream._internal.basic_types import SendableMessage
from faststream._internal.publisher.proto import BasePublisherProto
from faststream.rabbit.response import RabbitPublishCommand

if TYPE_CHECKING:
    from faststream._internal.basic_types import AsyncFunc
    from faststream._internal.publisher.proto import ProducerProto
    from faststream._internal.types import PublisherMiddleware
    from faststream.response.response import PublishCommand


class RabbitFakePublisher(BasePublisherProto):
    """Publisher Interface implementation to use as RPC or REPLY TO answer publisher."""

    def __init__(
        self,
        producer: "ProducerProto",
        routing_key: str,
        app_id: Optional[str],
    ) -> None:
        """Initialize an object."""
        self._producer = producer
        self.routing_key = routing_key
        self.app_id = str

    async def _publish(
        self,
        cmd: "PublishCommand",
        *,
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> Any:
        """This method should be called in subscriber flow only."""
        cmd = RabbitPublishCommand.from_cmd(cmd)
        cmd.destination = self.routing_key
        cmd.app_id = self.app_id

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
        msg = "You can't use `RabbitFakePublisher` directly."
        raise NotImplementedError(msg)

    async def request(
        self,
        message: "SendableMessage",
        /,
        *,
        correlation_id: Optional[str] = None,
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> Any:
        msg = (
            "`RabbitFakePublisher` can be used only to publish "
            "a response for `reply-to` or `RPC` messages."
        )
        raise NotImplementedError(msg)
