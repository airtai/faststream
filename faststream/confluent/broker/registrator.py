from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
    overload,
)

from confluent_kafka import Message
from fast_depends.dependencies import Depends
from typing_extensions import Annotated, Doc, deprecated, override

from faststream.broker.core.abc import ABCBroker
from faststream.broker.message import StreamMessage
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    PublisherMiddleware,
    SubscriberMiddleware,
)
from faststream.broker.utils import default_filter
from faststream.confluent.client import AsyncConfluentConsumer
from faststream.confluent.publisher.asyncapi import (
    AsyncAPIBatchPublisher,
    AsyncAPIDefaultPublisher,
    AsyncAPIPublisher,
)
from faststream.confluent.subscriber.asyncapi import (
    AsyncAPIBatchSubscriber,
    AsyncAPIDefaultSubscriber,
    AsyncAPISubscriber,
)
from faststream.exceptions import SetupError


class KafkaRegistrator(ABCBroker[Union[
    Message,
    Tuple[Message, ...],
]]):
    """Includable to KafkaBroker router."""

    _subscribers: Dict[int, Union[AsyncAPIBatchSubscriber, AsyncAPIDefaultSubscriber]]
    _publishers: Dict[int, Union[AsyncAPIBatchPublisher, AsyncAPIDefaultPublisher]]

    @override
    def subscriber(  # type: ignore[override]
        self,
        *topics: str,
        group_id: Optional[str] = None,
        key_deserializer: Optional[Callable[[bytes], Any]] = None,
        value_deserializer: Optional[Callable[[bytes], Any]] = None,
        fetch_max_wait_ms: int = 500,
        fetch_max_bytes: int = 52428800,
        fetch_min_bytes: int = 1,
        max_partition_fetch_bytes: int = 1 * 1024 * 1024,
        auto_offset_reset: Literal[
            "latest",
            "earliest",
            "none"
        ] = "latest",
        auto_commit: bool = True,
        auto_commit_interval_ms: int = 5 * 1000,
        check_crcs: bool = True,
        partition_assignment_strategy: Sequence[str] = (
            "roundrobin",
        ),
        max_poll_interval_ms: int = 5 * 60 * 1000,
        rebalance_timeout_ms: Optional[int] = None,
        session_timeout_ms: int = 10 * 1000,
        heartbeat_interval_ms: int = 3 * 1000,
        consumer_timeout_ms: int = 200,
        max_poll_records: Optional[int] = None,
        exclude_internal_topics: bool = True,
        isolation_level: Literal[
            "read_uncommitted",
            "read_committed"
        ] = "read_uncommitted",
        batch: bool = False,
        max_records: Optional[int] = None,
        batch_timeout_ms: int = 200,
        # broker args
        dependencies: Annotated[
            Iterable[Depends],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        parser: Annotated[
            Optional[
                Union[
                    CustomParser[Message],
                    CustomParser[Tuple[Message, ...]],
                ]
            ],
            Doc("Parser to map original **Message** object to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional[
                Union[
                    CustomDecoder[StreamMessage[Message]],
                    CustomDecoder[StreamMessage[Tuple[Message, ...]]],
                ]
            ],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        middlewares: Annotated[
            Iterable[SubscriberMiddleware],
            Doc("Subscriber middlewares to wrap incoming message processing."),
        ] = (),
        filter: Annotated[
            Union[
                Filter[StreamMessage[Message]],
                Filter[StreamMessage[Tuple[Message, ...]]],
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
        retry: Annotated[
            bool,
            Doc("Whether to `nack` message at processing exception."),
        ] = False,
        no_ack: Annotated[
            bool,
            Doc("Whether to disable **FastStream** autoacknowledgement logic or not."),
        ] = False,
        # AsyncAPI args
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
    ) -> AsyncAPISubscriber:
        if not auto_commit and not group_id:
            raise SetupError(
                "You should install `group_id` with manual commit mode")

        builder = partial(
            AsyncConfluentConsumer,
            key_deserializer=key_deserializer,
            value_deserializer=value_deserializer,
            fetch_max_wait_ms=fetch_max_wait_ms,
            fetch_max_bytes=fetch_max_bytes,
            fetch_min_bytes=fetch_min_bytes,
            max_partition_fetch_bytes=max_partition_fetch_bytes,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=auto_commit,
            auto_commit_interval_ms=auto_commit_interval_ms,
            check_crcs=check_crcs,
            partition_assignment_strategy=partition_assignment_strategy,
            max_poll_interval_ms=max_poll_interval_ms,
            rebalance_timeout_ms=rebalance_timeout_ms,
            session_timeout_ms=session_timeout_ms,
            heartbeat_interval_ms=heartbeat_interval_ms,
            consumer_timeout_ms=consumer_timeout_ms,
            max_poll_records=max_poll_records,
            exclude_internal_topics=exclude_internal_topics,
            isolation_level=isolation_level,
        )

        subcriber = cast(
            AsyncAPISubscriber,
            super().subscriber(
                AsyncAPISubscriber.create(
                    *topics,
                    batch=batch,
                    batch_timeout_ms=batch_timeout_ms,
                    max_records=max_records,
                    group_id=group_id,
                    builder=builder,
                    is_manual=not auto_commit,
                    # subscriber args
                    no_ack=no_ack,
                    retry=retry,
                    broker_middlewares=self._middlewares,
                    broker_dependencies=self._dependencies,
                    # AsyncAPI
                    title_=title,
                    description_=description,
                    include_in_schema=self._solve_include_in_schema(
                        include_in_schema),
                )
            ),
        )

        return subcriber.add_call(
            filter_=filter,
            parser_=parser or self._parser,
            decoder_=decoder or self._decoder,
            dependencies_=dependencies,
            middlewares_=middlewares,
        )

    @overload  # type: ignore[override]
    def publisher(
        self,
        topic: Annotated[
            str,
            Doc("Topic where the message will be published."),
        ],
        *,
        key: Annotated[
            Union[bytes, Any, None],
            Doc("""
            A key to associate with the message. Can be used to
            determine which partition to send the message to. If partition
            is `None` (and producer's partitioner config is left as default),
            then messages with the same key will be delivered to the same
            partition (but if key is `None`, partition is chosen randomly).
            Must be type `bytes`, or be serializable to bytes via configured
            `key_serializer`.
            """),
        ] = None,
        partition: Annotated[
            Optional[int],
            Doc("""
            Specify a partition. If not set, the partition will be
            selected using the configured `partitioner`.
            """),
        ] = None,
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
            Doc("Topic name to send response."),
        ] = "",
        batch: Annotated[
            Literal[False],
            Doc("Whether to send messages in batches or not."),
        ] = False,
        # basic args
        middlewares: Annotated[
            Iterable[PublisherMiddleware],
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
                "Should be any python-native object annotation or `pydantic.BaseModel`."
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
    ) -> AsyncAPIDefaultPublisher: ...

    @overload
    def publisher(
        self,
        topic: Annotated[
            str,
            Doc("Topic where the message will be published."),
        ],
        *,
        key: Annotated[
            Union[bytes, Any, None],
            Doc("""
            A key to associate with the message. Can be used to
            determine which partition to send the message to. If partition
            is `None` (and producer's partitioner config is left as default),
            then messages with the same key will be delivered to the same
            partition (but if key is `None`, partition is chosen randomly).
            Must be type `bytes`, or be serializable to bytes via configured
            `key_serializer`.
            """),
        ] = None,
        partition: Annotated[
            Optional[int],
            Doc("""
            Specify a partition. If not set, the partition will be
            selected using the configured `partitioner`.
            """),
        ] = None,
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
            Doc("Topic name to send response."),
        ] = "",
        batch: Annotated[
            Literal[True],
            Doc("Whether to send messages in batches or not."),
        ],
        # basic args
        middlewares: Annotated[
            Iterable[PublisherMiddleware],
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
                "Should be any python-native object annotation or `pydantic.BaseModel`."
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
    ) -> AsyncAPIBatchPublisher: ...

    @overload
    def publisher(
        self,
        topic: Annotated[
            str,
            Doc("Topic where the message will be published."),
        ],
        *,
        key: Annotated[
            Union[bytes, Any, None],
            Doc("""
            A key to associate with the message. Can be used to
            determine which partition to send the message to. If partition
            is `None` (and producer's partitioner config is left as default),
            then messages with the same key will be delivered to the same
            partition (but if key is `None`, partition is chosen randomly).
            Must be type `bytes`, or be serializable to bytes via configured
            `key_serializer`.
            """),
        ] = None,
        partition: Annotated[
            Optional[int],
            Doc("""
            Specify a partition. If not set, the partition will be
            selected using the configured `partitioner`.
            """),
        ] = None,
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
            Doc("Topic name to send response."),
        ] = "",
        batch: Annotated[
            bool,
            Doc("Whether to send messages in batches or not."),
        ] = False,
        # basic args
        middlewares: Annotated[
            Iterable[PublisherMiddleware],
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
                "Should be any python-native object annotation or `pydantic.BaseModel`."
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
    ) -> Union[
        AsyncAPIBatchPublisher,
        AsyncAPIDefaultPublisher,
    ]: ...

    @override
    def publisher(
        self,
        topic: Annotated[
            str,
            Doc("Topic where the message will be published."),
        ],
        *,
        key: Annotated[
            Union[bytes, Any, None],
            Doc("""
            A key to associate with the message. Can be used to
            determine which partition to send the message to. If partition
            is `None` (and producer's partitioner config is left as default),
            then messages with the same key will be delivered to the same
            partition (but if key is `None`, partition is chosen randomly).
            Must be type `bytes`, or be serializable to bytes via configured
            `key_serializer`.
            """),
        ] = None,
        partition: Annotated[
            Optional[int],
            Doc("""
            Specify a partition. If not set, the partition will be
            selected using the configured `partitioner`.
            """),
        ] = None,
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
            Doc("Topic name to send response."),
        ] = "",
        batch: Annotated[
            bool,
            Doc("Whether to send messages in batches or not."),
        ] = False,
        # basic args
        middlewares: Annotated[
            Iterable[PublisherMiddleware],
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
                "Should be any python-native object annotation or `pydantic.BaseModel`."
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = True,
    ) -> Union[
        AsyncAPIBatchPublisher,
        AsyncAPIDefaultPublisher,
    ]:
        """Creates long-living and AsyncAPI-documented publisher object.

        You can use it as a handler decorator (handler should be decorated by `@broker.subscriber(...)` too) - `@broker.publisher(...)`.
        In such case publisher will publish your handler return value.

        Or you can create a publisher object to call it lately - `broker.publisher(...).publish(...)`.
        """
        publisher = AsyncAPIPublisher.create(
            # batch flag
            batch=batch,
            # default args
            key=key,
            # both args
            topic=topic,
            partition=partition,
            headers=headers,
            reply_to=reply_to,
            # publisher-specific
            broker_middlewares=self._middlewares,
            middlewares=middlewares,
            # AsyncAPI
            title_=title,
            description_=description,
            schema_=schema,
            include_in_schema=self._solve_include_in_schema(include_in_schema),
        )

        if batch:
            return cast(AsyncAPIBatchPublisher, super().publisher(publisher))
        else:
            return cast(AsyncAPIDefaultPublisher, super().publisher(publisher))
