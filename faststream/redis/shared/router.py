from typing import Any, Callable, Sequence, Union

from faststream._compat import TypeAlias, model_copy, override
from faststream.broker.router import BrokerRoute as RedisRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.redis.message import AnyRedisDict
from faststream.redis.schemas import ListSub, PubSub, StreamSub
from faststream.types import SendableMessage

__all__ = (
    "RedisRouter",
    "RedisRoute",
)


Channel: TypeAlias = str


class RedisRouter(BrokerRouter[int, AnyRedisDict]):
    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[RedisRoute[AnyRedisDict, SendableMessage]] = (),
        **kwargs: Any,
    ):
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

        super().__init__(prefix, handlers, **kwargs)

    @override
    def subscriber(  # type: ignore[override]
        self,
        channel: Union[Channel, PubSub, None] = None,
        *,
        list: Union[Channel, ListSub, None] = None,
        stream: Union[Channel, StreamSub, None] = None,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[AnyRedisDict, P_HandlerParams, T_HandlerReturn],
    ]:
        channel = PubSub.validate(channel)
        list = ListSub.validate(list)
        stream = StreamSub.validate(stream)

        return self._wrap_subscriber(
            channel=model_copy(channel, update={"name": self.prefix + channel.name})
            if channel
            else None,
            list=model_copy(list, update={"name": self.prefix + list.name})
            if list
            else None,
            stream=model_copy(stream, update={"name": self.prefix + stream.name})
            if stream
            else None,
            **broker_kwargs,
        )
