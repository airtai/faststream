from faststream import Context
from faststream.redis import RedisBroker

broker = RedisBroker()

@broker.subscriber("test-channel")
async def handle(
    msg: str,
    collector: list[str] = Context(initial=list),
):
    collector.append(msg)
