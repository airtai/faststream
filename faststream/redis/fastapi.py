from faststream.broker.fastapi.router import StreamRouter
from faststream.redis.broker import RedisBroker
from faststream.redis.message import PubSubMessage


class RedisRouter(StreamRouter[PubSubMessage]):
    broker_class = RedisBroker

    @staticmethod
    def _setup_log_context(
        main_broker: RedisBroker,
        including_broker: RedisBroker,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(h.channel)
