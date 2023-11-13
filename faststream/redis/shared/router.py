from typing import Any, Callable, Sequence

from nats.aio.msg import Msg

from faststream._compat import override
from faststream.broker.router import BrokerRoute as RedisRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.redis.message import PubSubMessage
from faststream.types import SendableMessage

__all__ = (
    "RedisRouter",
    "RedisRoute",
)


class RedisRouter(BrokerRouter[str, PubSubMessage]):
    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[RedisRoute[PubSubMessage, SendableMessage]] = (),
        **kwargs: Any,
    ):
        for h in handlers:
            if not (channel := h.kwargs.pop("channel", None)):
                channel, h.args = h.args[0], h.args[1:]
            h.args = (prefix + channel, *h.args)
        super().__init__(prefix, handlers, **kwargs)

    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
    ]:
        return self._wrap_subscriber(  # type: ignore[return-value]
            self.prefix + subject,
            **broker_kwargs,
        )
