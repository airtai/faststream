from typing import TYPE_CHECKING, Any, Awaitable, Callable, Iterable, Optional, Union

from typing_extensions import Annotated, Doc, deprecated

from faststream.broker.router import ArgsContainer, BrokerRouter, SubscriberRoute
from faststream.broker.utils import default_filter
from faststream.redis.broker.registrator import RedisRegistrator
from faststream.redis.message import BaseMessage

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream.broker.types import (
        BrokerMiddleware,
        CustomCallable,
        Filter,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.redis.message import UnifyRedisMessage
    from faststream.redis.schemas import ListSub, PubSub, StreamSub
    from faststream.types import AnyDict, SendableMessage


class RedisPublisher(ArgsContainer):
    """Delayed RedisPublisher registration object.

    Just a copy of RedisRegistrator.publisher(...) arguments.
    """

    def __init__(
        self,
        channel: Annotated[
            Union["PubSub", str, None],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        *,
        list: Annotated[
            Union["ListSub", str, None],
            Doc("Redis List object name to send message."),
        ] = None,
        stream: Annotated[
            Union["StreamSub", str, None],
            Doc("Redis Stream object name to send message."),
        ] = None,
        headers: Annotated[
            Optional["AnyDict"],
            Doc(
                "Message headers to store metainformation. "
                "Can be overridden by `publish.headers` if specified."
            ),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("Reply message destination PubSub object name."),
        ] = "",
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
    ) -> None:
        super().__init__(
            channel=channel,
            list=list,
            stream=stream,
            headers=headers,
            reply_to=reply_to,
            middlewares=middlewares,
            title=title,
            description=description,
            schema=schema,
            include_in_schema=include_in_schema,
        )


class RedisRoute(SubscriberRoute):
    """Class to store delayed RedisBroker subscriber registration."""

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
        channel: Annotated[
            Union["PubSub", str, None],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        *,
        publishers: Annotated[
            Iterable["RedisPublisher"],
            Doc("Redis publishers to broadcast the handler result."),
        ] = (),
        list: Annotated[
            Union["ListSub", str, None],
            Doc("Redis List object name to send message."),
        ] = None,
        stream: Annotated[
            Union["StreamSub", str, None],
            Doc("Redis Stream object name to send message."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomCallable"],
            Doc(
                "Parser to map original **aio_pika.IncomingMessage** Msg to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomCallable"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware[UnifyRedisMessage]"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[UnifyRedisMessage]",
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
    ) -> None:
        super().__init__(
            call,
            channel=channel,
            publishers=publishers,
            list=list,
            stream=stream,
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


class RedisRouter(
    RedisRegistrator,
    BrokerRouter[BaseMessage],
):
    """Includable to RedisBroker router."""

    def __init__(
        self,
        prefix: Annotated[
            str,
            Doc("String prefix to add to all subscribers queues."),
        ] = "",
        handlers: Annotated[
            Iterable[RedisRoute],
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
            Iterable["BrokerMiddleware[BaseMessage]"],
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
