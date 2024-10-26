from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    Union,
)

from nats.aio.msg import Msg
from typing_extensions import Doc, override

from faststream._internal.publisher.usecase import PublisherUsecase
from faststream.message import gen_cor_id
from faststream.nats.response import NatsPublishCommand
from faststream.response.publish_type import PublishType

if TYPE_CHECKING:
    from faststream._internal.basic_types import SendableMessage
    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.nats.message import NatsMessage
    from faststream.nats.publisher.producer import NatsFastProducer, NatsJSFastProducer
    from faststream.nats.schemas import JStream
    from faststream.response.response import PublishCommand


class LogicPublisher(PublisherUsecase[Msg]):
    """A class to represent a NATS publisher."""

    _producer: Union["NatsFastProducer", "NatsJSFastProducer", None]

    def __init__(
        self,
        *,
        subject: str,
        reply_to: str,
        headers: Optional[dict[str, str]],
        stream: Optional["JStream"],
        timeout: Optional[float],
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        """Initialize NATS publisher object."""
        super().__init__(
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.subject = subject
        self.stream = stream
        self.timeout = timeout
        self.headers = headers or {}
        self.reply_to = reply_to

    @override
    async def publish(
        self,
        message: "SendableMessage",
        subject: str = "",
        *,
        headers: Optional[dict[str, str]] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
        stream: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """Publish message directly.

        Args:
            message (SendableMessage): Message body to send.
                Can be any encodable object (native python types or `pydantic.BaseModel`).
            subject (str): NATS subject to send message (default is `''`).
            headers (:obj:`dict` of :obj:`str`: :obj:`str`, optional): Message headers to store metainformation (default is `None`).
                **content-type** and **correlation_id** will be set automatically by framework anyway.

            reply_to (str): NATS subject name to send response (default is `None`).
            correlation_id (str, optional): Manual message **correlation_id** setter (default is `None`).
                **correlation_id** is a useful option to trace messages.

            stream (str, optional): This option validates that the target subject is in presented stream (default is `None`).
                Can be omitted without any effect.
            timeout (float, optional): Timeout to send message to NATS in seconds (default is `None`).
        """
        cmd = NatsPublishCommand(
            message,
            subject=subject or self.subject,
            headers=self.headers | (headers or {}),
            reply_to=reply_to or self.reply_to,
            correlation_id=correlation_id or gen_cor_id(),
            stream=stream or getattr(self.stream, "name", None),
            timeout=timeout or self.timeout,
            _publish_type=PublishType.Publish,
        )
        return await self._basic_publish(cmd, _extra_middlewares=())

    @override
    async def _publish(
        self,
        cmd: Union["PublishCommand", "NatsPublishCommand"],
        *,
        _extra_middlewares: Iterable["PublisherMiddleware"],
    ) -> None:
        """This method should be called in subscriber flow only."""
        cmd = NatsPublishCommand.from_cmd(cmd)

        cmd.destination = self.subject
        cmd.add_headers(self.headers, override=False)
        cmd.reply_to = cmd.reply_to or self.reply_to

        if self.stream:
            cmd.stream = self.stream.name
            cmd.timeout = self.timeout

        return await self._basic_publish(cmd, _extra_middlewares=_extra_middlewares)

    @override
    async def request(
        self,
        message: Annotated[
            "SendableMessage",
            Doc(
                "Message body to send. "
                "Can be any encodable object (native python types or `pydantic.BaseModel`).",
            ),
        ],
        subject: Annotated[
            str,
            Doc("NATS subject to send message."),
        ] = "",
        *,
        headers: Annotated[
            Optional[dict[str, str]],
            Doc(
                "Message headers to store metainformation. "
                "**content-type** and **correlation_id** will be set automatically by framework anyway.",
            ),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        timeout: Annotated[
            float,
            Doc("Timeout to send message to NATS."),
        ] = 0.5,
    ) -> "NatsMessage":
        cmd = NatsPublishCommand(
            message=message,
            subject=subject or self.subject,
            headers=self.headers | (headers or {}),
            timeout=timeout or self.timeout,
            correlation_id=correlation_id or gen_cor_id(),
            stream=getattr(self.stream, "name", None),
            _publish_type=PublishType.Request,
        )

        msg: NatsMessage = await self._basic_request(cmd)
        return msg

    def add_prefix(self, prefix: str) -> None:
        self.subject = prefix + self.subject
