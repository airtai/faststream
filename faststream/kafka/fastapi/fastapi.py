from typing import TYPE_CHECKING, Any, Callable, Iterable

from aiokafka import ConsumerRecord
from typing_extensions import Annotated, Doc

from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.core.publisher import BasePublisher
from faststream.broker.fastapi.router import StreamRouter
from faststream.broker.types import (
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.kafka.broker import KafkaBroker as KB

if TYPE_CHECKING:
    from fastapi import params


class KafkaRouter(StreamRouter[ConsumerRecord]):
    """A class to route Kafka streams.

    Attributes:
        broker_class : class representing the Kafka broker

    Methods:
        _setup_log_context : sets up the log context for the main broker and including broker
    """

    broker_class = KB

    def publisher(self, *args: Any, **kwargs: Any) -> BasePublisher[ConsumerRecord]:
        return self.broker.publisher(*args, **kwargs)

    def subscriber(
        self,
        *topics: str,
        dependencies: Annotated[
            Iterable["params.Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[ConsumerRecord, P_HandlerParams, T_HandlerReturn],
    ]:
        return super().subscriber(
            topics[0],
            *topics,
            dependencies=dependencies,
            **broker_kwargs,
        )
