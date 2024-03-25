from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Union

from typing_extensions import Annotated, Doc, TypeAlias, deprecated, override

from faststream.broker.core.broker import default_filter
from faststream.broker.router import BrokerRoute, BrokerRouter
from faststream.redis.asyncapi import Publisher
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BaseMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.types import AnyDict, SendableMessage


Channel: TypeAlias = str


class RedisRoute(BrokerRoute):
    """Class to store delaied RabbitBroker subscriber registration."""

    def __init__(
        self,
        call: Annotated[
            Callable[..., "SendableMessage"],
            Doc("Message handler function."),
        ],
        channel: Annotated[
            Union[Channel, PubSub, None],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        *,
        list: Annotated[
            Union[Channel, ListSub, None],
            Doc("Redis List object name to send message."),
        ] = None,
        stream: Annotated[
            Union[Channel, StreamSub, None],
            Doc("Redis Stream object name to send message."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[AnyDict]"],
            Doc(
                "Parser to map original **aio_pika.IncomingMessage** Msg to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[AnyDict]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[StreamMessage[AnyDict]]",
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
            channel=channel,
            list=list,
            stream=stream,
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

class RedisRouter(BrokerRouter["AnyDict"]):
    """A class to represent a Redis router."""
    _publishers: Dict[int, Publisher]  # type: ignore[assignment]

    def __init__(
        self,
        prefix: str = "",
        handlers: Iterable[RedisRoute] = (),
        *,
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to all routers' publishers/subscribers."),
        ] = (),
        middlewares: Annotated[
            Iterable[Callable[[Optional["AnyDict"]], "BaseMiddleware"]],
            Doc("Router middlewares to apply to all routers' publishers/subscribers."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[AnyDict]"],
            Doc(
                "Parser to map original **IncomingMessage** Msg to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[AnyDict]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        include_in_schema: Annotated[
            Optional[bool],
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = None,
    ) -> None:
        """Initialize the Redis router.

        Args:
            prefix: The prefix.
            handlers: The handlers.
            **kwargs: The keyword arguments.
        """
        for h in handlers:
            if not (channel := h.kwargs.pop("channel", None)):
                if list := h.kwargs.pop("list", None):
                    h.kwargs["list"] = prefix + list
                    continue

                elif stream := h.kwargs.pop("stream", None):
                    h.kwargs["stream"] = prefix + stream
                    continue

                channel, h.args = h.args[0], h.args[1:]

            h.args = (prefix + channel, *h.args)

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
        channel: Annotated[
            Union[Channel, PubSub, None],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        *,
        list: Annotated[
            Union[Channel, ListSub, None],
            Doc("Redis List object name to send message."),
        ] = None,
        stream: Annotated[
            Union[Channel, StreamSub, None],
            Doc("Redis Stream object name to send message."),
        ] = None,
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[AnyDict]"],
            Doc(
                "Parser to map original **aio_pika.IncomingMessage** Msg to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[Any]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable["SubscriberMiddleware"],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            "Filter[StreamMessage[Any]]",
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
        # Extra kwargs
        get_dependent: Annotated[
            Optional[Any],
            Doc("Service option to pass FastAPI-compatible callback."),
        ] = None,
    ) -> "WrapperProtocol[AnyDict]":
        if (channel := PubSub.validate(channel)):
            channel = deepcopy(channel)
            channel.name = self.prefix + channel.name

        if (list_sub := ListSub.validate(list)):
            list_sub = deepcopy(list_sub)
            list_sub.name = self.prefix + list_sub.name

        if (stream := StreamSub.validate(stream)):
            stream = deepcopy(stream)
            stream.name = self.prefix + stream.name

        return self._wrap_subscriber(
            channel=channel,
            list=list_sub,
            stream=stream,
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
        channel: Annotated[
            Union[Channel, PubSub, None],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        list: Annotated[
            Union[Channel, ListSub, None],
            Doc("Redis List object name to send message."),
        ] = None,
        stream: Annotated[
            Union[Channel, StreamSub, None],
            Doc("Redis Stream object name to send message."),
        ] = None,
        headers: Annotated[
            Optional["AnyDict"],
            Doc(
                "Message headers to store metainformation. "
                "Can be overrided by `publish.headers` if specified."
            ),
        ] = None,
        reply_to: Annotated[
            Optional[str],
            Doc("Reply message destination PubSub object name."),
        ] = None,
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
        if not any((stream, list, channel)):
            raise ValueError(INCORRECT_SETUP_MSG)

        new_publisher = self._update_publisher_prefix(
            self.prefix,
            Publisher(
                channel=PubSub.validate(channel),
                list=ListSub.validate(list),
                stream=StreamSub.validate(stream),
                reply_to=reply_to,
                headers=headers,
                middlewares=(
                    *(m(None).publish_scope for m in self._middlewares),
                    *middlewares
                ),
                # AsyncAPI options
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
        return publisher

    @override
    @staticmethod
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher:
        if (ch := publisher.channel) is not None:
            ch = deepcopy(ch)
            ch.name = prefix + ch.name
            publisher.channel = ch

        elif (l_sub := publisher.list) is not None:
            l_sub = deepcopy(l_sub)
            l_sub.name = prefix + l_sub.name
            publisher.list = l_sub

        elif (st := publisher.stream) is not None:
            st = deepcopy(st)
            st.name = prefix + st.name
            publisher.stream = st

        else:
            raise AssertionError("unreachable")

        return publisher
