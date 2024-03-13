from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Union

from typing_extensions import Annotated, Doc, deprecated, override

from faststream.broker.core.broker import default_filter
from faststream.broker.router import BrokerRoute, BrokerRouter
from faststream.rabbit.asyncapi import Publisher
from faststream.rabbit.publisher import PublishKwargs
from faststream.rabbit.schemas.schemas import (
    RabbitExchange,
    RabbitQueue,
)

if TYPE_CHECKING:
    from aio_pika.abc import DateType, HeadersType, TimeoutType
    from aio_pika.message import IncomingMessage
    from fast_depends.dependencies import Depends

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.types import (
        BaseMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.rabbit.message import RabbitMessage
    from faststream.rabbit.schemas.schemas import ReplyConfig
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.types import AnyDict


class RabbitRoute(BrokerRoute["IncomingMessage", "AioPikaSendableMessage"]):
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
            Doc(
                "Parser to map original **IncomingMessage** Msg to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[RabbitMessage]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[RabbitMessage]",
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
        # Extra kwargs
        get_dependent: Annotated[
            Optional[Any],
            Doc("Service option to pass FastAPI-compatible callback."),
        ] = None,
    ) -> None:
        super().__init__(
            call,
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
            get_dependent=get_dependent,
        )


class RabbitRouter(BrokerRouter[int, "IncomingMessage"]):
    _publishers: Dict[int, Publisher]

    def __init__(
        self,
        prefix: str = "",
        handlers: Iterable[RabbitRoute] = (),
        *,
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to all routers' publishers/subscribers."),
        ] = (),
        middlewares: Annotated[
            Iterable[Callable[[Optional["IncomingMessage"]], "BaseMiddleware"]],
            Doc("Router middlewares to apply to all routers' publishers/subscribers."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[IncomingMessage]"],
            Doc(
                "Parser to map original **IncomingMessage** Msg to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[RabbitMessage]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
    ) -> None:
        for h in handlers:
            if (q := h.kwargs.pop("queue", None)) is None:
                q, h.args = h.args[0], h.args[1:]
            new_q = deepcopy(RabbitQueue.validate(q))
            new_q.name = prefix + new_q.name
            h.args = (new_q, *h.args)

        super().__init__(
            prefix,
            handlers,
            dependencies=dependencies,
            middlewares=middlewares,
            parser=parser,
            decoder=decoder,
            include_in_schema=include_in_schema,
        )


    @override
    def subscriber(  # type: ignore[override]
        self,
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
            Doc(
                "Parser to map original **IncomingMessage** Msg to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[RabbitMessage]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[RabbitMessage]",
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
        # Extra kwargs
        get_dependent: Annotated[
            Optional[Any],
            Doc("Service option to pass FastAPI-compatible callback."),
        ] = None,
    ) -> "WrapperProtocol[IncomingMessage]":
        new_q = deepcopy(RabbitQueue.validate(queue))
        new_q.name = self.prefix + new_q.name
        return self._wrap_subscriber(
            new_q,
            exchange=exchange,
            consume_args=consume_args,
            reply_config=reply_config,
            # broker args
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
            get_dependent=get_dependent,
        )

    @override
    def publisher(  # type: ignore[override]
        self,
        queue: Annotated[
            Union[RabbitQueue, str],
            Doc("Default message routing key to publish with."),
        ] = "",
        exchange: Annotated[
            Union[RabbitExchange, str, None],
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
                "Client waits for confimation that the message is placed to some queue. "
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
            bool, Doc("Restore the message on RabbitMQ reboot."),
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
                "Can be overrided by `publish.headers` if specified."
            ),
        ] = None,
        content_type: Annotated[
            Optional[str],
            Doc(
                "Message **content-type** header. "
                "Used by application, not core RabbitMQ. "
                "Will be setted automatically if not specified."
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
    ) -> Publisher:
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

        new_publisher = self._update_publisher_prefix(
            self.prefix,
            Publisher(
                queue=RabbitQueue.validate(queue),
                exchange=RabbitExchange.validate(exchange),
                routing_key=routing_key,
                message_kwargs=message_kwargs,
                middlewares=(
                    *(m(None).publish_scope for m in self._middlewares),
                    *middlewares
                ),
                # AsyncAPI
                title_=title,
                description_=description,
                schema_=schema,
                include_in_schema=(
                    include_in_schema
                    if self.include_in_schema is None
                    else self.include_in_schema
                ),
                # delay setup
                virtual_host="",
                app_id="",
            ),
        )
        key = self._get_publisher_key(new_publisher)
        publisher = self._publishers[key] = self._publishers.get(key, new_publisher)
        return publisher

    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> int:
        return publisher._get_routing_hash()

    @staticmethod
    def _update_publisher_prefix(prefix: str, publisher: Publisher) -> Publisher:
        new_q = deepcopy(publisher.queue)
        new_q.name = prefix + new_q.name
        publisher.queue = new_q
        return publisher
