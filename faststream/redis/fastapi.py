from faststream._compat import override
from faststream.broker.fastapi.router import StreamRouter
from faststream.redis.broker import RedisBroker
from faststream.redis.message import AnyRedisDict


class RedisRouter(StreamRouter[AnyRedisDict]):
    broker_class = RedisBroker

    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: RedisBroker,
        including_broker: RedisBroker,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(h.channel_name)
