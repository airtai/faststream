from typing import Any, Callable, Sequence, Union

from aio_pika.message import IncomingMessage

from faststream._compat import model_copy, override
from faststream.broker.router import BrokerRoute as RabbitRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.rabbit.shared.schemas import RabbitQueue
from faststream.types import SendableMessage

__all__ = (
    "RabbitRoute",
    "RabbitRouter",
)


class RabbitRouter(BrokerRouter[int, IncomingMessage]):
    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[RabbitRoute[IncomingMessage, SendableMessage]] = (),
        **kwargs: Any,
    ):
        for h in handlers:
            q = RabbitQueue.validate(h.kwargs.pop("queue", h.args[0]))
            new_q = model_copy(q, update={"name": prefix + q.name})
            h.args = (new_q, *h.args[1:])

        super().__init__(prefix, handlers, **kwargs)

    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: Union[str, RabbitQueue],
        *broker_args: Any,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[IncomingMessage, P_HandlerParams, T_HandlerReturn],
    ]:
        q = RabbitQueue.validate(queue)
        new_q = model_copy(q, update={"name": self.prefix + q.name})
        return self._wrap_subscriber(new_q, *broker_args, **broker_kwargs)
