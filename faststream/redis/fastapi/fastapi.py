from typing import Any, Callable, Optional, Sequence, Union

from fastapi import Depends
from typing_extensions import override

from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.fastapi.router import StreamRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.redis.broker import RedisBroker as RB
from faststream.redis.schemas import PubSub


class RedisRouter(StreamRouter["AnyRedisDict"]):
    """A class to represent a Redis router."""

    broker_class = RB

    def subscriber(
        self,
        channel: Union[str, PubSub, None] = None,
        *,
        dependencies: Optional[Sequence[Depends]] = None,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        "HandlerCallWrapper[AnyRedisDict, P_HandlerParams, T_HandlerReturn]",
    ]:
        return super().subscriber(
            path=channel,
            dependencies=dependencies,
            **broker_kwargs,
        )

    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: RB,
        including_broker: RB,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(h.channel_name)
