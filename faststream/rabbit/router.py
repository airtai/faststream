from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional, Union

from typing_extensions import Annotated, Doc, deprecated

from faststream.broker.router import BrokerRouter, SubscriberRoute
from faststream.broker.utils import default_filter
from faststream.rabbit.broker.registrator import RabbitRegistrator
from faststream.rabbit.schemas import (
    RabbitExchange,
    RabbitQueue,
)

if TYPE_CHECKING:
    from aio_pika.message import IncomingMessage
    from broker.types import PublisherMiddleware
    from fast_depends.dependencies import Depends
    from rabbit.publisher.usecase import PublishKwargs

    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        SubscriberMiddleware,
    )
    from faststream.rabbit.schemas.reply import ReplyConfig
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.types import AnyDict


class RabbitPublisher:
    kwargs: dict[str, Any]

    def __init__(
            self,
            routing_key: str,
            queue: "RabbitQueue",
            exchange: Optional["RabbitExchange"],
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
        self.args = ()
        self.kwargs = dict(
            routing_key=routing_key,
            queue=queue,
            exchange=exchange,
            message_kwargs=message_kwargs,
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema
        )


class RabbitRoute(SubscriberRoute):
    """Class to store delaied RabbitBroker subscriber registration."""

    def __init__(
        self,
        call: Annotated[
            Callable[..., "AioPikaSendableMessage"],
            Doc("Message handler function."),
        ],
        queue: Annotated[
            Union[str, RabbitQueue],
            Doc(
                "RabbitMQ queue to listen. "
                "**FastStream** declares and binds queue object to `exchange` automatically if it is not passive (by default)."
            ),
        ],
        exchange: Annotated[
            Union[str, RabbitExchange, None],
            Doc(
                "RabbitMQ exchange to bind queue to. "
                "Uses default exchange if not presented. "
                "**FastStream** declares exchange object automatically if it is not passive (by default)."
            ),
        ] = None,
        *,
        publishers: Annotated[
            Optional[Iterable[RabbitPublisher]],
            Doc(
                "RabbitMQ producers to publish returned handlers results "
            )
        ] = (),
        consume_args: Annotated[
            Optional["AnyDict"],
            Doc("Extra consumer arguments to use in `queue.consume(...)` method."),
        ] = None,
        reply_config: Annotated[
            Optional["ReplyConfig"],
            Doc("Extra options to use at replies publishing."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[IncomingMessage]"],
            Doc("Parser to map original **IncomingMessage** Msg to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[IncomingMessage]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[StreamMessage[IncomingMessage]]",
            Doc(
                "Overload subscriber to consume various messages from the same source."
            ),
            deprecated(
                "Deprecated in **FastStream 0.5.0**. "
                "Please, create `subscriber` object and use it explicitly instead. "
                "Argument will be removed in **FastStream 0.6.0**."
            ),
        ] = default_filter,
        retry: Annotated[
            Union[bool, int],
            Doc("Whether to `nack` message at processing exception."),
        ] = False,
        no_ack: Annotated[
            bool,
            Doc("Whether to disable **FastStream** autoacknowledgement logic or not."),
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
    ) -> None:
        super().__init__(
            call,
            publishers=publishers,
            queue=queue,
            exchange=exchange,
            consume_args=consume_args,
            reply_config=reply_config,
            dependencies=dependencies,
            parser=parser,
            decoder=decoder,
            middlewares=middlewares,
            filter=filter,
            retry=retry,
            no_ack=no_ack,
            title=title,
            description=description,
            include_in_schema=include_in_schema,
        )


class RabbitRouter(
    BrokerRouter["IncomingMessage"],
    RabbitRegistrator,
):
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
            Iterable["Depends"],
            Doc(
                "Dependencies list (`[Depends(),]`) to apply to all routers' publishers/subscribers."
            ),
        ] = (),
        middlewares: Annotated[
            Iterable["BrokerMiddleware[IncomingMessage]"],
            Doc("Router middlewares to apply to all routers' publishers/subscribers."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[IncomingMessage]"],
            Doc("Parser to map original **IncomingMessage** Msg to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[IncomingMessage]]"],
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
            parser=parser,
            decoder=decoder,
            include_in_schema=include_in_schema,
        )
