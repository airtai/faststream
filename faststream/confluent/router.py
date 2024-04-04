from typing import Any, Callable, Iterable, Literal, Optional, Sequence, Tuple, Union

from confluent_kafka import Message
from fast_depends.dependencies import Depends
from typing_extensions import Annotated, Doc, deprecated

from faststream.broker.message import StreamMessage
from faststream.broker.router import BrokerRouter, SubscriberRoute
from faststream.broker.types import (
    BrokerMiddleware,
    CustomDecoder,
    CustomParser,
    Filter,
    SubscriberMiddleware,
)
from faststream.broker.utils import default_filter
from faststream.confluent.broker.registrator import KafkaRegistrator
from faststream.types import SendableMessage


class KafkaRoute(SubscriberRoute):
    """Class to store delaied KafkaBroker subscriber registration."""

    def __init__(
        self,
        call: Annotated[
            Callable[..., SendableMessage],
            Doc("Message handler function."),
        ],
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
            "none",
        ] = "latest",
        auto_commit: bool = True,
        auto_commit_interval_ms: int = 5000,
        check_crcs: bool = True,
        partition_assignment_strategy: Sequence[str] = (
            "roundrobin",
        ),
        max_poll_interval_ms: int = 300000,
        rebalance_timeout_ms: Optional[int] = None,
        session_timeout_ms: int = 10000,
        heartbeat_interval_ms: int = 3000,
        consumer_timeout_ms: int = 200,
        max_poll_records: Optional[int] = None,
        exclude_internal_topics: bool = True,
        isolation_level: Literal[
            "read_uncommitted",
            "read_committed",
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
    ) -> None:
        super().__init__(
            call,
            *topics,
            group_id=group_id,
            key_deserializer=key_deserializer,
            value_deserializer=value_deserializer,
            fetch_max_wait_ms=fetch_max_wait_ms,
            fetch_max_bytes=fetch_max_bytes,
            fetch_min_bytes=fetch_min_bytes,
            max_partition_fetch_bytes=max_partition_fetch_bytes,
            auto_offset_reset=auto_offset_reset,
            auto_commit=auto_commit,
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
            max_records=max_records,
            batch_timeout_ms=batch_timeout_ms,
            batch=batch,
            # basic args
            dependencies=dependencies,
            parser=parser,
            decoder=decoder,
            middlewares=middlewares,
            filter=filter,
            # AsyncAPI args
            title=title,
            description=description,
            include_in_schema=include_in_schema,
            # FastDepends args
            retry=retry,
            no_ack=no_ack,
        )


class KafkaRouter(
    BrokerRouter[Union[
        Message,
        Tuple[Message, ...],
    ]],
    KafkaRegistrator,
):
    """Includable to KafkaBroker router."""

    def __init__(
        self,
        prefix: Annotated[
            str,
            Doc("String prefix to add to all subscribers queues."),
        ] = "",
        handlers: Annotated[
            Iterable[KafkaRoute],
            Doc("Route object to include."),
        ] = (),
        *,
        dependencies: Annotated[
            Iterable[Depends],
            Doc(
                "Dependencies list (`[Depends(),]`) to apply to all routers' publishers/subscribers."
            ),
        ] = (),
        middlewares: Annotated[
            Iterable[Union[
                BrokerMiddleware[Message],
                BrokerMiddleware[Tuple[Message, ...]],
            ]],
            Doc("Router middlewares to apply to all routers' publishers/subscribers."),
        ] = (),
        parser: Annotated[
            Optional[Union[
                CustomParser[Message],
                CustomParser[Tuple[Message, ...]],
            ]],
            Doc("Parser to map original **Message** object to FastStream one."),
        ] = None,
        decoder: Annotated[
            Optional[Union[
                CustomDecoder[StreamMessage[Message]],
                CustomDecoder[StreamMessage[Tuple[Message, ...]]],
            ]],
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
