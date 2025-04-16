from typing import TYPE_CHECKING, Optional, Union

from typing_extensions import Unpack, override

from faststream.rabbit.schemas.exchange import RabbitExchange
from faststream.response import PublishCommand, Response
from faststream.response.publish_type import PublishType

if TYPE_CHECKING:
    from typing import TypedDict

    from aio_pika.abc import TimeoutType

    from faststream.rabbit.publisher.options import MessageOptions
    from faststream.rabbit.types import AioPikaSendableMessage

    class _PublishOptions(TypedDict):
        timeout: TimeoutType
        mandatory: bool
        immediate: bool


class RabbitResponse(Response):
    def __init__(
        self,
        body: "AioPikaSendableMessage",
        *,
        timeout: "TimeoutType" = None,
        mandatory: bool = True,
        immediate: bool = False,
        **message_options: Unpack["MessageOptions"],
    ) -> None:
        headers = message_options.pop("headers", {})
        correlation_id = message_options.pop("correlation_id", None)

        super().__init__(
            body=body,
            headers=headers,
            correlation_id=correlation_id,
        )

        self.message_options = message_options
        self.publish_options: _PublishOptions = {
            "mandatory": mandatory,
            "immediate": immediate,
            "timeout": timeout,
        }

    @override
    def as_publish_command(self) -> "RabbitPublishCommand":
        return RabbitPublishCommand(  # type: ignore[misc]
            message=self.body,
            headers=self.headers,
            correlation_id=self.correlation_id,
            _publish_type=PublishType.PUBLISH,
            # RMQ specific
            routing_key="",
            **self.publish_options,
            **self.message_options,
        )


class RabbitPublishCommand(PublishCommand):
    def __init__(
        self,
        message: "AioPikaSendableMessage",
        *,
        _publish_type: PublishType,
        routing_key: str = "",
        exchange: Optional[RabbitExchange] = None,
        # publish kwargs
        mandatory: bool = True,
        immediate: bool = False,
        timeout: "TimeoutType" = None,
        **message_options: Unpack["MessageOptions"],
    ) -> None:
        headers = message_options.pop("headers", {})
        reply_to = message_options.pop("reply_to", None) or ""
        correlation_id = message_options.pop("correlation_id", None)

        super().__init__(
            body=message,
            destination=routing_key,
            correlation_id=correlation_id,
            headers=headers,
            reply_to=reply_to,
            _publish_type=_publish_type,
        )
        self.exchange = exchange or RabbitExchange()

        self.timeout = timeout

        self.message_options = message_options
        self.publish_options = {
            "mandatory": mandatory,
            "immediate": immediate,
        }

    @classmethod
    def from_cmd(
        cls,
        cmd: Union["PublishCommand", "RabbitPublishCommand"],
    ) -> "RabbitPublishCommand":
        if isinstance(cmd, RabbitPublishCommand):
            # NOTE: Should return a copy probably.
            return cmd

        return cls(
            message=cmd.body,
            routing_key=cmd.destination,
            correlation_id=cmd.correlation_id,
            headers=cmd.headers,
            reply_to=cmd.reply_to,
            _publish_type=cmd.publish_type,
        )
