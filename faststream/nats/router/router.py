from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Union,
)

from nats.js import api
from typing_extensions import Annotated, Doc, deprecated, override

from faststream.broker.core.broker import default_filter
from faststream.broker.router import BrokerRoute, BrokerRouter
from faststream.nats.asyncapi import Publisher
from faststream.nats.helpers import stream_builder

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends
    from nats.aio.msg import Msg

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.nats.schemas import JStream, PullSub
    from faststream.types import SendableMessage


class NatsRoute(BrokerRoute):
    """Class to store delaied NatsBroker subscriber registration."""

    def __init__(
        self,
        call: Annotated[
            Callable[..., "SendableMessage"],
            Doc("Message handler function."),
        ],
        subject: Annotated[
            str,
            Doc("NATS subject to subscribe."),
        ],
        queue: Annotated[
            str,
            Doc(
                "Subscribers' NATS queue name. Subscribers with same queue name will be load balanced by the NATS "
                "server."
            ),
        ] = "",
        pending_msgs_limit: Annotated[
            Optional[int],
            Doc(
                "Limit of messages, considered by NATS server as possible to be delivered to the client without "
                "been answered. In case of NATS Core, if that limits exceeds, you will receive NATS 'Slow Consumer' "
                "error. "
                "That's literally means that your worker can't handle the whole load. In case of NATS JetStream, "
                "you will no longer receive messages until some of delivered messages will be acked in any way."
            ),
        ] = None,
        pending_bytes_limit: Annotated[
            Optional[int],
            Doc(
                "The number of bytes, considered by NATS server as possible to be delivered to the client without "
                "been answered. In case of NATS Core, if that limit exceeds, you will receive NATS 'Slow Consumer' "
                "error."
                "That's literally means that your worker can't handle the whole load. In case of NATS JetStream, "
                "you will no longer receive messages until some of delivered messages will be acked in any way."
            ),
        ] = None,
        # Core arguments
        max_msgs: Annotated[
            int,
            Doc("Consuming messages limiter. Automatically disconnect if reached."),
        ] = 0,
        # JS arguments
        durable: Annotated[
            Optional[str],
            Doc(
                "Name of the durable consumer to which the the subscription should be bound."
            ),
        ] = None,
        config: Annotated[
            Optional["api.ConsumerConfig"],
            Doc("Configuration of JetStream consumer to be subscribed with."),
        ] = None,
        ordered_consumer: Annotated[
            bool,
            Doc("Enable ordered consumer mode."),
        ] = False,
        idle_heartbeat: Annotated[
            Optional[float],
            Doc("Enable Heartbeats for a consumer to detect failures."),
        ] = None,
        flow_control: Annotated[
            bool,
            Doc("Enable Flow Control for a consumer."),
        ] = False,
        deliver_policy: Annotated[
            Optional["api.DeliverPolicy"],
            Doc("Deliver Policy to be used for subscription."),
        ] = None,
        headers_only: Annotated[
            Optional[bool],
            Doc(
                "Should be message delivered without payload, only headers and metadata."
            ),
        ] = None,
        # pull arguments
        pull_sub: Annotated[
            Optional["PullSub"],
            Doc(
                "NATS Pull consumer parameters container. "
                "Should be used with `stream` only."
            ),
        ] = None,
        inbox_prefix: Annotated[
            bytes,
            Doc(
                "Prefix for generating unique inboxes, subjects with that prefix and NUID."
            ),
        ] = api.INBOX_PREFIX,
        # custom
        ack_first: Annotated[
            bool,
            Doc("Whether to `ack` message at start of consuming or not."),
        ] = False,
        stream: Annotated[
            Union[str, "JStream", None],
            Doc("Subscribe to NATS Stream with `subject` filter."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[Msg]"],
            Doc("Parser to map original **nats-py** Msg to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[Msg]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[StreamMessage[Msg]]",
            Doc(
                "Overload subscriber to consume various messages from the same source."
            ),
            deprecated(
                "Deprecated in **FastStream 0.5.0**. "
                "Please, create `subscriber` object and use it explicitly instead. "
                "Argument will be removed in **FastStream 0.6.0**."
            ),
        ] = default_filter,
        max_workers: Annotated[
            int,
            Doc("Number of workers to process messages concurrently."),
        ] = 1,
        retry: Annotated[
            bool,
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
            subject=subject,
            queue=queue,
            pending_msgs_limit=pending_msgs_limit,
            pending_bytes_limit=pending_bytes_limit,
            max_msgs=max_msgs,
            ordered_consumer=ordered_consumer,
            idle_heartbeat=idle_heartbeat,
            deliver_policy=deliver_policy,
            flow_control=flow_control,
            headers_only=headers_only,
            pull_sub=pull_sub,
            inbox_prefix=inbox_prefix,
            durable=durable,
            ack_first=ack_first,
            stream=stream,
            config=config,
            max_workers=max_workers,
            # broker args
            dependencies=dependencies,
            parser=parser,
            decoder=decoder,
            middlewares=middlewares,
            filter=filter,
            retry=retry,
            no_ack=no_ack,
            get_dependent=get_dependent,
            # AsyncAPI args
            title=title,
            description=description,
            include_in_schema=include_in_schema,
        )

class NatsRouter(BrokerRouter["Msg"]):
    """A class to represent a NATS router."""

    _publishers: Dict[int, Publisher]

    def __init__(
        self,
        prefix: str = "",
        handlers: Iterable[NatsRoute] = (),
        *,
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to all routers' publishers/subscribers."),
        ] = (),
        middlewares: Annotated[
            Iterable["BrokerMiddleware[Msg]"],
            Doc("Router middlewares to apply to all routers' publishers/subscribers."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[Msg]"],
            Doc(
                "Parser to map original nats-py **Msg** to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[Msg]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        include_in_schema: Annotated[
        Optional[bool],
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = None,
    ) -> None:
        for h in handlers:
            if not (subj := h.kwargs.pop("subject", None)):
                subj, h.args = h.args[0], h.args[1:]
            h.args = (prefix + subj, *h.args)
        super().__init__(prefix, handlers, dependencies=dependencies, middlewares=middlewares,
                         parser=parser, decoder=decoder, include_in_schema=include_in_schema,)

    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: Annotated[
            str,
            Doc("NATS subject to subscribe."),
        ],
        queue: Annotated[
            str,
            Doc(
                "Subscribers' NATS queue name. Subscribers with same queue name will be load balanced by the NATS "
                "server."
            ),
        ] = "",
        pending_msgs_limit: Annotated[
            Optional[int],
            Doc(
                "Limit of messages, considered by NATS server as possible to be delivered to the client without "
                "been answered. In case of NATS Core, if that limits exceeds, you will receive NATS 'Slow Consumer' "
                "error. "
                "That's literally means that your worker can't handle the whole load. In case of NATS JetStream, "
                "you will no longer receive messages until some of delivered messages will be acked in any way."
            ),
        ] = None,
        pending_bytes_limit: Annotated[
            Optional[int],
            Doc(
                "The number of bytes, considered by NATS server as possible to be delivered to the client without "
                "been answered. In case of NATS Core, if that limit exceeds, you will receive NATS 'Slow Consumer' "
                "error."
                "That's literally means that your worker can't handle the whole load. In case of NATS JetStream, "
                "you will no longer receive messages until some of delivered messages will be acked in any way."
            ),
        ] = None,
        # Core arguments
        max_msgs: Annotated[
            int,
            Doc("Consuming messages limiter. Automatically disconnect if reached."),
        ] = 0,
        # JS arguments
        durable: Annotated[
            Optional[str],
            Doc(
                "Name of the durable consumer to which the the subscription should be bound."
            ),
        ] = None,
        config: Annotated[
            Optional["api.ConsumerConfig"],
            Doc("Configuration of JetStream consumer to be subscribed with."),
        ] = None,
        ordered_consumer: Annotated[
            bool,
            Doc("Enable ordered consumer mode."),
        ] = False,
        idle_heartbeat: Annotated[
            Optional[float],
            Doc("Enable Heartbeats for a consumer to detect failures."),
        ] = None,
        flow_control: Annotated[
            bool,
            Doc("Enable Flow Control for a consumer."),
        ] = False,
        deliver_policy: Annotated[
            Optional["api.DeliverPolicy"],
            Doc("Deliver Policy to be used for subscription."),
        ] = None,
        headers_only: Annotated[
            Optional[bool],
            Doc(
                "Should be message delivered without payload, only headers and metadata."
            ),
        ] = None,
        # pull arguments
        pull_sub: Annotated[
            Optional["PullSub"],
            Doc(
                "NATS Pull consumer parameters container. "
                "Should be used with `stream` only."
            ),
        ] = None,
        inbox_prefix: Annotated[
            bytes,
            Doc(
                "Prefix for generating unique inboxes, subjects with that prefix and NUID."
            ),
        ] = api.INBOX_PREFIX,
        # custom
        ack_first: Annotated[
            bool,
            Doc("Whether to `ack` message at start of consuming or not."),
        ] = False,
        stream: Annotated[
            Union[str, "JStream", None],
            Doc("Subscribe to NATS Stream with `subject` filter."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[Msg]"],
            Doc("Parser to map original **nats-py** Msg to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[Msg]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[StreamMessage[Msg]]",
            Doc(
                "Overload subscriber to consume various messages from the same source."
            ),
            deprecated(
                "Deprecated in **FastStream 0.5.0**. "
                "Please, create `subscriber` object and use it explicitly instead. "
                "Argument will be removed in **FastStream 0.6.0**."
            ),
        ] = default_filter,
        max_workers: Annotated[
            int,
            Doc("Number of workers to process messages concurrently."),
        ] = 1,
        retry: Annotated[
            bool,
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
    ) -> "WrapperProtocol[Msg]":
        return self._wrap_subscriber(
            self.prefix + subject,
            queue=queue,
            pending_msgs_limit=pending_msgs_limit,
            pending_bytes_limit=pending_bytes_limit,
            max_msgs=max_msgs,
            durable=durable,
            config=config,
            ordered_consumer=ordered_consumer,
            idle_heartbeat=idle_heartbeat,
            flow_control=flow_control,
            deliver_policy=deliver_policy,
            headers_only=headers_only,
            pull_sub=pull_sub,
            inbox_prefix=inbox_prefix,
            ack_first=ack_first,
            stream=stream,
            dependencies=dependencies,
            parser=parser,
            decoder=decoder,
            middlewares=middlewares,
            filter=filter,
            max_workers=max_workers,
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
        subject: Annotated[
            str,
            Doc("NATS subject to send message."),
        ],
        headers: Annotated[
            Optional[Dict[str, str]],
            Doc(
                "Message headers to store metainformation. "
                "**content-type** and **correlation_id** will be setted automatically by framework anyway. "
                "Can be overrided by `publish.headers` if specified."
            ),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("NATS subject name to send response."),
        ] = "",
        # JS
        stream: Annotated[
            Union[str, "JStream", None],
            Doc(
                "This option validates that the target `subject` is in presented stream. "
                "Can be ommited without any effect."
            ),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc("Timeout to send message to NATS."),
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
    ) -> Publisher:
        new_publisher = self._update_publisher_prefix(
            self.prefix,
            Publisher(
                subject=subject,
                reply_to=reply_to,
                stream=stream_builder.stream(stream),
                headers=headers,
                middlewares=(
                    *(m(None).publish_scope for m in self._middlewares),
                    *middlewares
                ),
                timeout=timeout,
                # AsyncAPI information
                title_=title,
                description_=description,
                schema_=schema,
                include_in_schema=(
                    include_in_schema
                    if self.include_in_schema is None
                    else self.include_in_schema
                ),
            ),
        )
        publisher_key = hash(new_publisher)
        publisher = self._publishers[publisher_key] = self._publishers.get(
            publisher_key, new_publisher
        )

        if publisher.stream is not None:
            publisher.stream.add_subject(publisher.subject)

        return publisher

    @override
    @staticmethod
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher:
        publisher.subject = prefix + publisher.subject
        return publisher
