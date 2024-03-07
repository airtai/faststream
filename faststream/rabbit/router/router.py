from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Union

from typing_extensions import Annotated, Doc, override

from faststream._compat import model_copy
from faststream.broker.router import BrokerRoute as RabbitRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.rabbit.asyncapi import Publisher
from faststream.rabbit.publisher import PublishKwargs
from faststream.rabbit.schemas.schemas import (
    RabbitExchange,
    RabbitQueue,
)

if TYPE_CHECKING:
    from aio_pika.abc import DateType, HeadersType, TimeoutType
    from aio_pika.message import IncomingMessage

    from faststream.broker.core.call_wrapper import HandlerCallWrapper
    from faststream.broker.types import PublisherMiddleware
    from faststream.types import SendableMessage


class RabbitRouter(BrokerRouter[int, "IncomingMessage"]):
    _publishers: Dict[int, Publisher]

    def __init__(
        self,
        prefix: str = "",
        handlers: Iterable[RabbitRoute["IncomingMessage", "SendableMessage"]] = (),
        **kwargs: Any,
    ) -> None:
        for h in handlers:
            if (q := h.kwargs.pop("queue", None)) is None:
                q, h.args = h.args[0], h.args[1:]
            queue = RabbitQueue.validate(q)
            new_q = model_copy(queue, update={"name": prefix + queue.name})
            h.args = (new_q, *h.args)

        super().__init__(prefix, handlers, **kwargs)

    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: Union[str, RabbitQueue],
        *broker_args: Any,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        "HandlerCallWrapper[IncomingMessage, P_HandlerParams, T_HandlerReturn]",
    ]:
        q = RabbitQueue.validate(queue)
        new_q = model_copy(q, update={"name": self.prefix + q.name})
        return self._wrap_subscriber(new_q, *broker_args, **broker_kwargs)

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
                middlewares=middlewares,
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
        publisher.queue = model_copy(
            publisher.queue, update={"name": prefix + publisher.queue.name}
        )
        return publisher
