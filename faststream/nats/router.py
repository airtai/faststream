from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Optional,
    Sequence,
    Union,
)

from nats.js import api
from typing_extensions import Annotated, Doc, deprecated

from faststream.broker.router import ArgsContainer, BrokerRouter, SubscriberRoute
from faststream.broker.utils import default_filter
from faststream.nats.broker.registrator import NatsRegistrator

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends
    from nats.aio.msg import Msg

    from faststream.broker.types import (
        BrokerMiddleware,
        CustomCallable,
        Filter,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.nats.message import NatsBatchMessage, NatsMessage
    from faststream.nats.schemas import JStream, KvWatch, ObjWatch, PullSub
    from faststream.types import SendableMessage


class NatsPublisher(ArgsContainer):
    """Delayed NatsPublisher registration object.

    Just a copy of `KafkaRegistrator.publisher(...)` arguments.
    """

    def __init__(
        self,
        subject: Annotated[
            str,
            Doc("NATS subject to send message."),
        ],
        *,
        headers: Annotated[
            Optional[Dict[str, str]],
            Doc(
                "Message headers to store metainformation. "
                "**content-type** and **correlation_id** will be set automatically by framework anyway. "
                "Can be overridden by `publish.headers` if specified."
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
                "Can be omitted without any effect."
            ),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc("Timeout to send message to NATS."),
        ] = None,
        # basic args
        middlewares: Annotated[
            Sequence["PublisherMiddleware"],
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
    ) -> None:
        super().__init__(
            subject=subject,
            headers=headers,
            reply_to=reply_to,
            stream=stream,
            timeout=timeout,
            middlewares=middlewares,
            title=title,
            description=description,
            schema=schema,
            include_in_schema=include_in_schema,
        )


class NatsRoute(SubscriberRoute):
    """Class to store delayed NatsBroker subscriber registration."""

    def __init__(
        self,
        call: Annotated[
            Union[
                Callable[..., "SendableMessage"],
                Callable[..., Awaitable["SendableMessage"]],
            ],
            Doc(
                "Message handler function "
                "to wrap the same with `@broker.subscriber(...)` way."
            ),
        ],
        subject: Annotated[
            str,
            Doc("NATS subject to subscribe."),
        ],
        publishers: Annotated[
            Iterable[NatsPublisher],
            Doc("Nats publishers to broadcast the handler result."),
        ] = (),
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
            Optional[bool],
            Doc("Enable Flow Control for a consumer."),
        ] = None,
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
        kv_watch: Annotated[
            Union[str, "KvWatch", None],
            Doc("KeyValue watch parameters container."),
        ] = None,
        obj_watch: Annotated[
            Union[bool, "ObjWatch"],
            Doc("ObjecStore watch parameters container."),
        ] = False,
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
            Optional["CustomCallable"],
            Doc("Parser to map original **nats-py** Msg to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional["CustomCallable"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Sequence["SubscriberMiddleware[NatsMessage]"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            Union[
                "Filter[NatsMessage]",
                "Filter[NatsBatchMessage]",
            ],
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
    ) -> None:
        super().__init__(
            call,
            subject=subject,
            publishers=publishers,
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
            kv_watch=kv_watch,
            obj_watch=obj_watch,
            inbox_prefix=inbox_prefix,
            ack_first=ack_first,
            stream=stream,
            max_workers=max_workers,
            queue=queue,
            dependencies=dependencies,
            parser=parser,
            decoder=decoder,
            middlewares=middlewares,
            filter=filter,
            retry=retry,
            no_ack=no_ack,
            no_reply=no_reply,
            title=title,
            description=description,
            include_in_schema=include_in_schema,
        )


class NatsRouter(
    NatsRegistrator,
    BrokerRouter["Msg"],
):
    """Includable to NatsBroker router."""

    def __init__(
        self,
        prefix: Annotated[
            str,
            Doc("String prefix to add to all subscribers subjects."),
        ] = "",
        handlers: Annotated[
            Iterable[NatsRoute],
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
            Sequence["BrokerMiddleware[Msg]"],
            Doc("Router middlewares to apply to all routers' publishers/subscribers."),
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
            parser=parser,
            decoder=decoder,
            include_in_schema=include_in_schema,
        )
