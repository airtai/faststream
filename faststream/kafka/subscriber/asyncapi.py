from typing import (
    TYPE_CHECKING,
    Dict,
    Iterable,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

from typing_extensions import override

from faststream.asyncapi.schema import (
    Channel,
    ChannelBinding,
    CorrelationId,
    Message,
    Operation,
)
from faststream.asyncapi.schema.bindings import kafka
from faststream.asyncapi.utils import resolve_payloads
from faststream.broker.types import MsgType
from faststream.exceptions import SetupError
from faststream.kafka.subscriber.usecase import (
    BatchSubscriber,
    DefaultSubscriber,
    LogicSubscriber,
)

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord, TopicPartition
    from aiokafka.abc import ConsumerRebalanceListener
    from fast_depends.dependencies import Depends

    from faststream.broker.types import BrokerMiddleware
    from faststream.types import AnyDict


class AsyncAPISubscriber(LogicSubscriber[MsgType]):
    """A class to handle logic and async API operations."""

    def get_name(self) -> str:
        return f'{",".join(self.topics)}:{self.call_name}'

    def get_schema(self) -> Dict[str, Channel]:
        channels = {}

        payloads = self.get_payloads()

        for t in self.topics:
            handler_name = self.title_ or f"{t}:{self.call_name}"

            channels[handler_name] = Channel(
                description=self.description,
                subscribe=Operation(
                    message=Message(
                        title=f"{handler_name}:Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    kafka=kafka.ChannelBinding(topic=t),
                ),
            )

        return channels

    @overload  # type: ignore[override]
    @staticmethod
    def create(
        *topics: str,
        batch: Literal[True],
        batch_timeout_ms: int,
        max_records: Optional[int],
        # Kafka information
        group_id: Optional[str],
        listener: Optional["ConsumerRebalanceListener"],
        pattern: Optional[str],
        connection_args: "AnyDict",
        partitions: Iterable["TopicPartition"],
        is_manual: bool,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[Tuple[ConsumerRecord, ...]]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> "AsyncAPIBatchSubscriber": ...

    @overload
    @staticmethod
    def create(
        *topics: str,
        batch: Literal[False],
        batch_timeout_ms: int,
        max_records: Optional[int],
        # Kafka information
        group_id: Optional[str],
        listener: Optional["ConsumerRebalanceListener"],
        pattern: Optional[str],
        connection_args: "AnyDict",
        partitions: Iterable["TopicPartition"],
        is_manual: bool,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[ConsumerRecord]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> "AsyncAPIDefaultSubscriber": ...

    @overload
    @staticmethod
    def create(
        *topics: str,
        batch: bool,
        batch_timeout_ms: int,
        max_records: Optional[int],
        # Kafka information
        group_id: Optional[str],
        listener: Optional["ConsumerRebalanceListener"],
        pattern: Optional[str],
        connection_args: "AnyDict",
        partitions: Iterable["TopicPartition"],
        is_manual: bool,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable[
            "BrokerMiddleware[Union[ConsumerRecord, Tuple[ConsumerRecord, ...]]]"
        ],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> Union[
        "AsyncAPIDefaultSubscriber",
        "AsyncAPIBatchSubscriber",
    ]: ...

    @override
    @staticmethod
    def create(
        *topics: str,
        batch: bool,
        batch_timeout_ms: int,
        max_records: Optional[int],
        # Kafka information
        group_id: Optional[str],
        listener: Optional["ConsumerRebalanceListener"],
        pattern: Optional[str],
        connection_args: "AnyDict",
        partitions: Iterable["TopicPartition"],
        is_manual: bool,
        # Subscriber args
        no_ack: bool,
        retry: bool,
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable[
            "BrokerMiddleware[Union[ConsumerRecord, Tuple[ConsumerRecord, ...]]]"
        ],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> Union[
        "AsyncAPIDefaultSubscriber",
        "AsyncAPIBatchSubscriber",
    ]:
        if is_manual and not group_id:
            raise SetupError("You should install `group_id` with manual commit mode")

        if not topics and not partitions and not pattern:
            raise SetupError(
                "You should provide either `topics` or `partitions` or `pattern`."
            )
        elif topics and partitions:
            raise SetupError("You can't provide both `topics` and `partitions`.")
        elif topics and pattern:
            raise SetupError("You can't provide both `topics` and `pattern`.")
        elif pattern and partitions:
            raise SetupError("You can't provide both `pattern` and `partitions`.")

        if batch:
            return AsyncAPIBatchSubscriber(
                *topics,
                batch_timeout_ms=batch_timeout_ms,
                max_records=max_records,
                group_id=group_id,
                listener=listener,
                pattern=pattern,
                connection_args=connection_args,
                partitions=partitions,
                is_manual=is_manual,
                no_ack=no_ack,
                retry=retry,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )
        else:
            return AsyncAPIDefaultSubscriber(
                *topics,
                group_id=group_id,
                listener=listener,
                pattern=pattern,
                connection_args=connection_args,
                partitions=partitions,
                is_manual=is_manual,
                no_ack=no_ack,
                retry=retry,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )


class AsyncAPIDefaultSubscriber(
    DefaultSubscriber,
    AsyncAPISubscriber["ConsumerRecord"],
):
    pass


class AsyncAPIBatchSubscriber(
    BatchSubscriber,
    AsyncAPISubscriber[Tuple["ConsumerRecord", ...]],
):
    pass
