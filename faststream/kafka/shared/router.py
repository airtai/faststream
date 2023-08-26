from typing import Any, Callable, Sequence

from aiokafka import ConsumerRecord

from faststream.broker.router import BrokerRoute as KafkaRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.types import SendableMessage

__all__ = (
    "BrokerRouter",
    "KafkaRoute",
)


class KafkaRouter(BrokerRouter[str, ConsumerRecord]):
    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[KafkaRoute[ConsumerRecord, SendableMessage]] = (),
        **kwargs: Any,
    ):
        for h in handlers:
            h.args = tuple(prefix + x for x in h.args)
        super().__init__(prefix, handlers, **kwargs)

    def subscriber(
        self,
        *topics: str,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[ConsumerRecord, P_HandlerParams, T_HandlerReturn],
    ]:
        return self._wrap_subscriber(
            *(self.prefix + x for x in topics),
            **broker_kwargs,
        )
