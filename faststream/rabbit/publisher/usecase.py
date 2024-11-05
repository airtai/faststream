from collections.abc import Iterable
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Optional,
    Union,
)

from aio_pika import IncomingMessage
from typing_extensions import Doc, Unpack, override

from faststream._internal.publisher.usecase import PublisherUsecase
from faststream._internal.utils.data import filter_by_dict
from faststream.message import gen_cor_id
from faststream.rabbit.response import RabbitPublishCommand
from faststream.rabbit.schemas import BaseRMQInformation, RabbitExchange, RabbitQueue
from faststream.response.publish_type import PublishType

from .options import MessageOptions, PublishOptions

if TYPE_CHECKING:
    import aiormq

    from faststream._internal.setup import SetupState
    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.rabbit.message import RabbitMessage
    from faststream.rabbit.publisher.producer import AioPikaFastProducer
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.response.response import PublishCommand


# should be public to use in imports
class RequestPublishKwargs(MessageOptions, PublishOptions, total=False):
    """Typed dict to annotate RabbitMQ requesters."""


class PublishKwargs(MessageOptions, PublishOptions, total=False):
    """Typed dict to annotate RabbitMQ publishers."""

    reply_to: Annotated[
        Optional[str],
        Doc(
            "Reply message routing key to send with (always sending to default exchange).",
        ),
    ]


class LogicPublisher(
    PublisherUsecase[IncomingMessage],
    BaseRMQInformation,
):
    """A class to represent a RabbitMQ publisher."""

    app_id: Optional[str]

    _producer: Optional["AioPikaFastProducer"]

    def __init__(
        self,
        *,
        routing_key: str,
        queue: "RabbitQueue",
        exchange: "RabbitExchange",
        # PublishCommand options
        message_kwargs: "PublishKwargs",
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[IncomingMessage]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.routing_key = routing_key

        request_options = dict(message_kwargs)
        self.headers = request_options.pop("headers") or {}
        self.reply_to = request_options.pop("reply_to", "")
        self.timeout = request_options.pop("timeout", None)
        self.message_options = filter_by_dict(MessageOptions, request_options)
        self.publish_options = filter_by_dict(PublishOptions, request_options)

        # BaseRMQInformation
        self.queue = queue
        self.exchange = exchange

        # Setup it later
        self.app_id = None
        self.virtual_host = ""

    @override
    def _setup(  # type: ignore[override]
        self,
        *,
        producer: Optional["AioPikaFastProducer"],
        app_id: Optional[str],
        virtual_host: str,
        state: "SetupState",
    ) -> None:
        if app_id:
            self.message_options["app_id"] = app_id
            self.app_id = app_id

        self.virtual_host = virtual_host

        super()._setup(producer=producer, state=state)

    @property
    def routing(self) -> str:
        """Return real routing_key of Publisher."""
        return self.routing_key or self.queue.routing

    @override
    async def publish(
        self,
        message: "AioPikaSendableMessage",
        queue: Annotated[
            Union["RabbitQueue", str, None],
            Doc("Message routing key to publish with."),
        ] = None,
        exchange: Annotated[
            Union["RabbitExchange", str, None],
            Doc("Target exchange to publish message to."),
        ] = None,
        *,
        routing_key: Annotated[
            str,
            Doc(
                "Message routing key to publish with. "
                "Overrides `queue` option if presented.",
            ),
        ] = "",
        # message args
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        # publisher specific
        **publish_kwargs: "Unpack[PublishKwargs]",
    ) -> Optional["aiormq.abc.ConfirmationFrameType"]:
        if not routing_key:
            if q := RabbitQueue.validate(queue):
                routing_key = q.routing
            else:
                routing_key = self.routing

        headers = self.headers | publish_kwargs.pop("headers", {})
        cmd = RabbitPublishCommand(
            message,
            routing_key=routing_key,
            exchange=RabbitExchange.validate(exchange or self.exchange),
            correlation_id=correlation_id or gen_cor_id(),
            headers=headers,
            _publish_type=PublishType.Publish,
            **(self.publish_options | self.message_options | publish_kwargs),
        )

        frame: Optional[aiormq.abc.ConfirmationFrameType] = await self._basic_publish(
            cmd,
            _extra_middlewares=(),
        )
        return frame

    @override
    async def _publish(
        self,
        cmd: Union["RabbitPublishCommand", "PublishCommand"],
        *,
        _extra_middlewares: Iterable["PublisherMiddleware"],
    ) -> None:
        """This method should be called in subscriber flow only."""
        cmd = RabbitPublishCommand.from_cmd(cmd)

        cmd.destination = self.routing
        cmd.reply_to = cmd.reply_to or self.reply_to
        cmd.add_headers(self.headers, override=False)

        cmd.timeout = cmd.timeout or self.timeout

        cmd.message_options = {**self.message_options, **cmd.message_options}
        cmd.publish_options = {**self.publish_options, **cmd.publish_options}

        await self._basic_publish(cmd, _extra_middlewares=_extra_middlewares)

    @override
    async def request(
        self,
        message: "AioPikaSendableMessage",
        queue: Annotated[
            Union["RabbitQueue", str, None],
            Doc("Message routing key to publish with."),
        ] = None,
        exchange: Annotated[
            Union["RabbitExchange", str, None],
            Doc("Target exchange to publish message to."),
        ] = None,
        *,
        routing_key: Annotated[
            str,
            Doc(
                "Message routing key to publish with. "
                "Overrides `queue` option if presented.",
            ),
        ] = "",
        # message args
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        # publisher specific
        **publish_kwargs: "Unpack[RequestPublishKwargs]",
    ) -> "RabbitMessage":
        if not routing_key:
            if q := RabbitQueue.validate(queue):
                routing_key = q.routing
            else:
                routing_key = self.routing

        headers = self.headers | publish_kwargs.pop("headers", {})
        cmd = RabbitPublishCommand(
            message,
            routing_key=routing_key,
            exchange=RabbitExchange.validate(exchange or self.exchange),
            correlation_id=correlation_id or gen_cor_id(),
            headers=headers,
            _publish_type=PublishType.Publish,
            **(self.publish_options | self.message_options | publish_kwargs),
        )

        msg: RabbitMessage = await self._basic_request(cmd)
        return msg

    def add_prefix(self, prefix: str) -> None:
        """Include Publisher in router."""
        new_q = deepcopy(self.queue)
        new_q.name = prefix + new_q.name
        self.queue = new_q
