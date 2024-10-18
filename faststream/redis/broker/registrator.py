from collections.abc import Iterable
from typing import TYPE_CHECKING, Annotated, Any, Optional, Union, cast

from typing_extensions import Doc, override

from faststream._internal.broker.abc_broker import ABCBroker
from faststream.redis.message import UnifyRedisDict
from faststream.redis.publisher.factory import create_publisher
from faststream.redis.publisher.specified import SpecificationPublisher
from faststream.redis.subscriber.factory import SubsciberType, create_subscriber
from faststream.redis.subscriber.specified import SpecificationSubscriber

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.types import (
        CustomCallable,
        PublisherMiddleware,
        SubscriberMiddleware,
    )
    from faststream.redis.message import UnifyRedisMessage
    from faststream.redis.publisher.specified import PublisherType
    from faststream.redis.schemas import ListSub, PubSub, StreamSub


class RedisRegistrator(ABCBroker[UnifyRedisDict]):
    """Includable to RedisBroker router."""

    _subscribers: list["SubsciberType"]
    _publishers: list["PublisherType"]

    @override
    def subscriber(  # type: ignore[override]
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
        # broker arguments
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional["CustomCallable"],
            Doc(
                "Parser to map original **aio_pika.IncomingMessage** Msg to FastStream one.",
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
    ) -> SpecificationSubscriber:
        subscriber = cast(
            SpecificationSubscriber,
            super().subscriber(
                create_subscriber(
                    channel=channel,
                    list=list,
                    stream=stream,
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
                ),
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
                "Can be overridden by `publish.headers` if specified.",
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
                "Should be any python-native object annotation or `pydantic.BaseModel`.",
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
    ) -> "SpecificationPublisher":
        """Creates long-living and AsyncAPI-documented publisher object.

        You can use it as a handler decorator (handler should be decorated by `@broker.subscriber(...)` too) - `@broker.publisher(...)`.
        In such case publisher will publish your handler return value.

        Or you can create a publisher object to call it lately - `broker.publisher(...).publish(...)`.
        """
        return cast(
            SpecificationPublisher,
            super().publisher(
                create_publisher(
                    channel=channel,
                    list=list,
                    stream=stream,
                    headers=headers,
                    reply_to=reply_to,
                    # Specific
                    broker_middlewares=self._middlewares,
                    middlewares=middlewares,
                    # AsyncAPI
                    title_=title,
                    description_=description,
                    schema_=schema,
                    include_in_schema=self._solve_include_in_schema(include_in_schema),
                ),
            ),
        )
