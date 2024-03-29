from typing import Any, Callable, Sequence

from confluent_kafka import Message

from faststream.broker.router import BrokerRoute as KafkaRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.types import SendableMessage

__all__ = (
    "BrokerRouter",
    "KafkaRoute",
)


class KafkaRouter(BrokerRouter[str, Message]):
    """A class to represent a Kafka router.

    Attributes:
        prefix : prefix for the topics
        handlers : sequence of Kafka routes
        kwargs : additional keyword arguments

    Methods:
        subscriber : decorator for subscribing to topics and handling messages

    """

    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[KafkaRoute[Message, SendableMessage]] = (),
        **kwargs: Any,
    ) -> None:
        """Initialize the class.

        Args:
            prefix (str): Prefix string.
            handlers (Sequence[KafkaRoute[confluent_kafka.Message, SendableMessage]]): Sequence of KafkaRoute objects.
            **kwargs (Any): Additional keyword arguments.

        """
        for h in handlers:
            h.args = tuple(prefix + x for x in h.args)
        super().__init__(prefix, handlers, **kwargs)

    def subscriber(
        self,
        *topics: str,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Message, P_HandlerParams, T_HandlerReturn],
    ]:
        """A function to subscribe to topics.

        Args:
            *topics : variable number of topic names
            **broker_kwargs : keyword arguments for the broker

        Returns:
            A callable function that wraps the handler function

        """
        return self._wrap_subscriber(
            *(self.prefix + x for x in topics),
            **broker_kwargs,
        )
