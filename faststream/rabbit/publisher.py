from contextlib import AsyncExitStack
from itertools import chain
from typing import TYPE_CHECKING, Any, Iterable, Optional, Union

from aio_pika import IncomingMessage
from typing_extensions import Annotated, Doc, TypedDict, Unpack, override

from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.rabbit.handler import LogicHandler
from faststream.rabbit.schemas.schemas import BaseRMQInformation, RabbitQueue
from faststream.types import SendableMessage

if TYPE_CHECKING:
    import aiormq
    from aio_pika.abc import DateType, HeadersType, TimeoutType

    from faststream.broker.types import PublisherMiddleware
    from faststream.rabbit.producer import AioPikaFastProducer
    from faststream.rabbit.schemas.schemas import RabbitExchange
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.types import AnyDict, SendableMessage


# should be public to use in imports
class PublishKwargs(TypedDict, total=False):
    """Typed dict to annotate RabbitMQ publishers."""
    headers: Annotated[
        Optional["HeadersType"],
        Doc(
            "Message headers to store metainformation. "
            "Can be overrided by `publish.headers` if specified."
        ),
    ]
    mandatory: Annotated[
        Optional[bool],
        Doc(
            "Client waits for confimation that the message is placed to some queue. "
            "RabbitMQ returns message to client if there is no suitable queue."
        ),
    ]
    immediate: Annotated[
        Optional[bool],
        Doc(
            "Client expects that there is consumer ready to take the message to work. "
            "RabbitMQ returns message to client if there is no suitable consumer."
        ),
    ]
    timeout: Annotated[
        "TimeoutType",
        Doc("Send confirmation time from RabbitMQ."),
    ]
    persist: Annotated[
        Optional[bool], Doc("Restore the message on RabbitMQ reboot."),
    ]
    reply_to: Annotated[
        Optional[str],
        Doc(
            "Reply message routing key to send with (always sending to default exchange)."
        ),
    ]
    priority: Annotated[
        Optional[int],
        Doc("The message priority (0 by default)."),
    ]
    message_type: Annotated[
        Optional[str],
        Doc("Application-specific message type, e.g. **orders.created**."),
    ]
    content_type: Annotated[
        Optional[str],
        Doc(
            "Message **content-type** header. "
            "Used by application, not core RabbitMQ. "
            "Will be setted automatically if not specified."
        ),
    ]
    user_id: Annotated[
        Optional[str],
        Doc("Publisher connection User ID, validated if set."),
    ]
    expiration: Annotated[
        Optional["DateType"],
        Doc("Message expiration (lifetime) in seconds (or datetime or timedelta)."),
    ]
    content_encoding: Annotated[
        Optional[str],
        Doc("Message body content encoding, e.g. **gzip**."),
    ]


class LogicPublisher(
    BasePublisher[IncomingMessage],
    BaseRMQInformation,
):
    """A class to represent a RabbitMQ publisher."""

    _producer: Optional["AioPikaFastProducer"]

    def __init__(
        self,
        *,
        app_id: str,
        routing_key: str,
        virtual_host: str,
        queue: "RabbitQueue",
        exchange: Optional["RabbitExchange"],
        message_kwargs: "PublishKwargs",
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
        self.message_kwargs = message_kwargs

        self._producer = None

        # BaseRMQInformation
        self.app_id = app_id
        self.queue = queue
        self.exchange = exchange
        self.virtual_host = virtual_host

    @property
    def routing(self) -> str:
        return self.routing_key or self.queue.routing

    def __hash__(self) -> int:
        return LogicHandler.get_routing_hash(self.queue, self.exchange) + hash(
            self.routing_key
        )

    @override
    async def publish(  # type: ignore[override]
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
                "Overrides `queue` option if presented."
            ),
        ] = "",
        # message args
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages."
            ),
        ] = None,
        message_id: Annotated[
            Optional[str],
            Doc("Arbitrary message id. Generated automatically if not presented."),
        ] = None,
        timestamp: Annotated[
            Optional["DateType"],
            Doc("Message publish timestamp. Generated automatically if not presented."),
        ] = None,
        # rps args
        rpc: Annotated[
            bool,
            Doc("Whether to wait for reply in blocking mode."),
        ] = False,
        rpc_timeout: Annotated[
            Optional[float],
            Doc("RPC reply waiting time."),
        ] = 30.0,
        raise_timeout: Annotated[
            bool,
            Doc(
                "Whetever to raise `TimeoutError` or return `None` at **rpc_timeout**. "
                "RPC request returns `None` at timeout by default."
            ),
        ] = False,
        # publisher specific
        extra_middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Extra middlewares to wrap publishing process."),
        ] = (),
        **publish_kwargs: "Unpack[PublishKwargs]"
    ) -> Union["aiormq.abc.ConfirmationFrameType", "SendableMessage"]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs: "AnyDict" = {
            "routing_key": routing_key or self.routing_key or RabbitQueue.validate(queue or self.queue).routing,
            "exchange": exchange or self.exchange,
            "app_id": self.app_id,
            "correlation_id": correlation_id,
            "message_id": message_id,
            "timestamp": timestamp,
            # specific args
            "rpc": rpc,
            "rpc_timeout": rpc_timeout,
            "raise_timeout": raise_timeout,
            **self.message_kwargs,
            **publish_kwargs,
        }

        async with AsyncExitStack() as stack:
            for m in chain(extra_middlewares, self.middlewares):
                message = await stack.enter_async_context(
                    m(message, **kwargs)
                )

            return await self._producer.publish(message=message, **kwargs)

        raise AssertionError("unreachable")

