from collections.abc import Awaitable, Iterable, Sequence
from typing import TYPE_CHECKING, Annotated, Any, Callable, Optional, Union

from typing_extensions import Doc, deprecated

from faststream._internal.broker.router import (
    ArgsContainer,
    BrokerRouter,
    SubscriberRoute,
)
from faststream._internal.constants import EMPTY
from faststream.middlewares import AckPolicy
from faststream.rabbit.broker.registrator import RabbitRegistrator

if TYPE_CHECKING:
    from aio_pika.abc import DateType, HeadersType, TimeoutType
    from aio_pika.message import IncomingMessage
    from fast_depends.dependencies import Dependant

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.broker.abc_broker import ABCBroker
    from faststream._internal.types import (
        BrokerMiddleware,
        CustomCallable,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.rabbit.message import RabbitMessage
    from faststream.rabbit.schemas import (
        RabbitExchange,
        RabbitQueue,
    )
    from faststream.rabbit.types import AioPikaSendableMessage


class RabbitPublisher(ArgsContainer):
    """Delayed RabbitPublisher registration object.

    Just a copy of `RabbitRegistrator.publisher(...)` arguments.
    """

    def __init__(
        self,
        queue: Annotated[
            Union["RabbitQueue", str],
            Doc("Default message routing key to publish with."),
        ] = "",
        exchange: Annotated[
            Union["RabbitExchange", str, None],
            Doc("Target exchange to publish message to."),
        ] = None,
        *,
        routing_key: Annotated[
            str,
            Doc(
                "Default message routing key to publish with. "
                "Overrides `queue` option if presented.",
            ),
        ] = "",
        mandatory: Annotated[
            bool,
            Doc(
                "Client waits for confirmation that the message is placed to some queue. "
                "RabbitMQ returns message to client if there is no suitable queue.",
            ),
        ] = True,
        immediate: Annotated[
            bool,
            Doc(
                "Client expects that there is consumer ready to take the message to work. "
                "RabbitMQ returns message to client if there is no suitable consumer.",
            ),
        ] = False,
        timeout: Annotated[
            "TimeoutType",
            Doc("Send confirmation time from RabbitMQ."),
        ] = None,
        persist: Annotated[
            bool,
            Doc("Restore the message on RabbitMQ reboot."),
        ] = False,
        reply_to: Annotated[
            Optional[str],
            Doc(
                "Reply message routing key to send with (always sending to default exchange).",
            ),
        ] = None,
        priority: Annotated[
            Optional[int],
            Doc("The message priority (0 by default)."),
        ] = None,
        # basic args
        middlewares: Annotated[
            Sequence["PublisherMiddleware"],
            deprecated(
                "This option was deprecated in 0.6.0. Use router-level middlewares instead."
                "Scheduled to remove in 0.7.0"
            ),
            Doc("Publisher middlewares to wrap outgoing messages."),
        ] = (),
        # AsyncAPI args
        title: Annotated[
            Optional[str],
            Doc("AsyncAPI publisher object title."),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc("AsyncAPI publisher object description."),
        ] = None,
        schema: Annotated[
            Optional[Any],
            Doc(
                "AsyncAPI publishing message type. "
                "Should be any python-native object annotation or `pydantic.BaseModel`.",
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
        # message args
        headers: Annotated[
            Optional["HeadersType"],
            Doc(
                "Message headers to store metainformation. "
                "Can be overridden by `publish.headers` if specified.",
            ),
        ] = None,
        content_type: Annotated[
            Optional[str],
            Doc(
                "Message **content-type** header. "
                "Used by application, not core RabbitMQ. "
                "Will be set automatically if not specified.",
            ),
        ] = None,
        content_encoding: Annotated[
            Optional[str],
            Doc("Message body content encoding, e.g. **gzip**."),
        ] = None,
        expiration: Annotated[
            Optional["DateType"],
            Doc("Message expiration (lifetime) in seconds (or datetime or timedelta)."),
        ] = None,
        message_type: Annotated[
            Optional[str],
            Doc("Application-specific message type, e.g. **orders.created**."),
        ] = None,
        user_id: Annotated[
            Optional[str],
            Doc("Publisher connection User ID, validated if set."),
        ] = None,
    ) -> None:
        super().__init__(
            queue=queue,
            exchange=exchange,
            routing_key=routing_key,
            mandatory=mandatory,
            immediate=immediate,
            timeout=timeout,
            persist=persist,
            reply_to=reply_to,
            priority=priority,
            headers=headers,
            content_type=content_type,
            content_encoding=content_encoding,
            expiration=expiration,
            message_type=message_type,
            user_id=user_id,
            # basic args
            middlewares=middlewares,
            # AsyncAPI args
            title=title,
            description=description,
            schema=schema,
            include_in_schema=include_in_schema,
        )


class RabbitRoute(SubscriberRoute):
    """Class to store delayed RabbitBroker subscriber registration.

    Just a copy of `RabbitRegistrator.subscriber(...)` arguments.
    """

    def __init__(
        self,
        call: Annotated[
            Union[
                Callable[..., "AioPikaSendableMessage"],
                Callable[..., Awaitable["AioPikaSendableMessage"]],
            ],
            Doc(
                "Message handler function "
                "to wrap the same with `@broker.subscriber(...)` way.",
            ),
        ],
        queue: Annotated[
            Union[str, "RabbitQueue"],
            Doc(
                "RabbitMQ queue to listen. "
                "**FastStream** declares and binds queue object to `exchange` automatically if it is not passive (by default).",
            ),
        ],
        exchange: Annotated[
            Union[str, "RabbitExchange", None],
            Doc(
                "RabbitMQ exchange to bind queue to. "
                "Uses default exchange if not presented. "
                "**FastStream** declares exchange object automatically if it is not passive (by default).",
            ),
        ] = None,
        *,
        publishers: Annotated[
            Iterable[RabbitPublisher],
            Doc("RabbitMQ publishers to broadcast the handler result."),
        ] = (),
        consume_args: Annotated[
            Optional["AnyDict"],
            Doc("Extra consumer arguments to use in `queue.consume(...)` method."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Dependant"],
            Doc("Dependencies list (`[Dependant(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomCallable"],
            Doc("Parser to map original **IncomingMessage** Msg to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional["CustomCallable"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Sequence["SubscriberMiddleware[RabbitMessage]"],
            deprecated(
                "This option was deprecated in 0.6.0. Use router-level middlewares instead."
                "Scheduled to remove in 0.7.0"
            ),
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        no_ack: Annotated[
            bool,
            Doc("Whether to disable **FastStream** auto acknowledgement logic or not."),
            deprecated(
                "This option was deprecated in 0.6.0 to prior to **ack_policy=AckPolicy.DO_NOTHING**. "
                "Scheduled to remove in 0.7.0"
            ),
        ] = EMPTY,
        ack_policy: AckPolicy = EMPTY,
        no_reply: Annotated[
            bool,
            Doc(
                "Whether to disable **FastStream** RPC and Reply To auto responses or not.",
            ),
        ] = False,
        # AsyncAPI information
        title: Annotated[
            Optional[str],
            Doc("AsyncAPI subscriber object title."),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc(
                "AsyncAPI subscriber object description. "
                "Uses decorated docstring as default.",
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
    ) -> None:
        super().__init__(
            call,
            publishers=publishers,
            queue=queue,
            exchange=exchange,
            consume_args=consume_args,
            dependencies=dependencies,
            parser=parser,
            decoder=decoder,
            middlewares=middlewares,
            ack_policy=ack_policy,
            no_ack=no_ack,
            no_reply=no_reply,
            title=title,
            description=description,
            include_in_schema=include_in_schema,
        )


class RabbitRouter(RabbitRegistrator, BrokerRouter["IncomingMessage"]):
    """Includable to RabbitBroker router."""

    def __init__(
        self,
        prefix: Annotated[
            str,
            Doc("String prefix to add to all subscribers queues."),
        ] = "",
        handlers: Annotated[
            Iterable[RabbitRoute],
            Doc("Route object to include."),
        ] = (),
        *,
        dependencies: Annotated[
            Iterable["Dependant"],
            Doc(
                "Dependencies list (`[Dependant(),]`) to apply to all routers' publishers/subscribers.",
            ),
        ] = (),
        middlewares: Annotated[
            Sequence["BrokerMiddleware[IncomingMessage]"],
            Doc("Router middlewares to apply to all routers' publishers/subscribers."),
        ] = (),
        routers: Annotated[
            Sequence["ABCBroker[IncomingMessage]"],
            Doc("Routers to apply to broker."),
        ] = (),
        parser: Annotated[
            Optional["CustomCallable"],
            Doc("Parser to map original **IncomingMessage** Msg to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional["CustomCallable"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        include_in_schema: Annotated[
            Optional[bool],
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = None,
    ) -> None:
        super().__init__(
            handlers=handlers,
            # basic args
            prefix=prefix,
            dependencies=dependencies,
            middlewares=middlewares,
            routers=routers,
            parser=parser,
            decoder=decoder,
            include_in_schema=include_in_schema,
        )
