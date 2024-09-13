from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union, cast

from typing_extensions import Annotated, Doc, override

from faststream._internal.broker.abc_broker import ABCBroker
from faststream.rabbit.publisher.publisher import SpecificationPublisher
from faststream.rabbit.publisher.usecase import PublishKwargs
from faststream.rabbit.schemas import (
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.subscriber.factory import create_subscriber
from faststream.rabbit.subscriber.subscriber import SpecificationSubscriber

if TYPE_CHECKING:
    from aio_pika import IncomingMessage  # noqa: F401
    from aio_pika.abc import DateType, HeadersType, TimeoutType
    from fast_depends.dependencies import Depends

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.types import (
        CustomCallable,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.rabbit.message import RabbitMessage


class RabbitRegistrator(ABCBroker["IncomingMessage"]):
    """Includable to RabbitBroker router."""

    _subscribers: Dict[int, "SpecificationSubscriber"]
    _publishers: Dict[int, "SpecificationPublisher"]

    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: Annotated[
            Union[str, "RabbitQueue"],
            Doc(
                "RabbitMQ queue to listen. "
                "**FastStream** declares and binds queue object to `exchange` automatically if it is not passive (by default)."
            ),
        ],
        exchange: Annotated[
            Union[str, "RabbitExchange", None],
            Doc(
                "RabbitMQ exchange to bind queue to. "
                "Uses default exchange if not presented. "
                "**FastStream** declares exchange object automatically if it is not passive (by default)."
            ),
        ] = None,
        *,
        consume_args: Annotated[
            Optional["AnyDict"],
            Doc("Extra consumer arguments to use in `queue.consume(...)` method."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
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
            Iterable["SubscriberMiddleware[RabbitMessage]"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        retry: Annotated[
            Union[bool, int],
            Doc("Whether to `nack` message at processing exception."),
        ] = False,
        no_ack: Annotated[
            bool,
            Doc("Whether to disable **FastStream** autoacknowledgement logic or not."),
        ] = False,
        no_reply: Annotated[
            bool,
            Doc(
                "Whether to disable **FastStream** RPC and Reply To auto responses or not."
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
                "Uses decorated docstring as default."
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
    ) -> SpecificationSubscriber:
        subscriber = cast(
            SpecificationSubscriber,
            super().subscriber(
                create_subscriber(
                    queue=RabbitQueue.validate(queue),
                    exchange=RabbitExchange.validate(exchange),
                    consume_args=consume_args,
                    # subscriber args
                    no_ack=no_ack,
                    no_reply=no_reply,
                    retry=retry,
                    broker_middlewares=self._middlewares,
                    broker_dependencies=self._dependencies,
                    # AsyncAPI
                    title_=title,
                    description_=description,
                    include_in_schema=self._solve_include_in_schema(include_in_schema),
                )
            ),
        )

        return subscriber.add_call(
            parser_=parser or self._parser,
            decoder_=decoder or self._decoder,
            dependencies_=dependencies,
            middlewares_=middlewares,
        )

    @override
    def publisher(  # type: ignore[override]
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
                "Overrides `queue` option if presented."
            ),
        ] = "",
        mandatory: Annotated[
            bool,
            Doc(
                "Client waits for confirmation that the message is placed to some queue. "
                "RabbitMQ returns message to client if there is no suitable queue."
            ),
        ] = True,
        immediate: Annotated[
            bool,
            Doc(
                "Client expects that there is consumer ready to take the message to work. "
                "RabbitMQ returns message to client if there is no suitable consumer."
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
                "Reply message routing key to send with (always sending to default exchange)."
            ),
        ] = None,
        priority: Annotated[
            Optional[int],
            Doc("The message priority (0 by default)."),
        ] = None,
        # specific
        middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Publisher middlewares to wrap outgoing messages."),
        ] = (),
        # AsyncAPI information
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
                "Should be any python-native object annotation or `pydantic.BaseModel`."
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
                "Can be overridden by `publish.headers` if specified."
            ),
        ] = None,
        content_type: Annotated[
            Optional[str],
            Doc(
                "Message **content-type** header. "
                "Used by application, not core RabbitMQ. "
                "Will be set automatically if not specified."
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
    ) -> SpecificationPublisher:
        """Creates long-living and AsyncAPI-documented publisher object.

        You can use it as a handler decorator (handler should be decorated by `@broker.subscriber(...)` too) - `@broker.publisher(...)`.
        In such case publisher will publish your handler return value.

        Or you can create a publisher object to call it lately - `broker.publisher(...).publish(...)`.
        """
        message_kwargs = PublishKwargs(
            mandatory=mandatory,
            immediate=immediate,
            timeout=timeout,
            persist=persist,
            reply_to=reply_to,
            headers=headers,
            priority=priority,
            content_type=content_type,
            content_encoding=content_encoding,
            message_type=message_type,
            user_id=user_id,
            expiration=expiration,
        )

        publisher = cast(
            SpecificationPublisher,
            super().publisher(
                SpecificationPublisher.create(
                    routing_key=routing_key,
                    queue=RabbitQueue.validate(queue),
                    exchange=RabbitExchange.validate(exchange),
                    message_kwargs=message_kwargs,
                    # Specific
                    broker_middlewares=self._middlewares,
                    middlewares=middlewares,
                    # AsyncAPI
                    title_=title,
                    description_=description,
                    schema_=schema,
                    include_in_schema=self._solve_include_in_schema(include_in_schema),
                )
            ),
        )

        return publisher
