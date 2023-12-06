from faststream import Context, FastStream
from faststream.redis import RedisBroker

broker = RedisBroker("redis://localhost:6379")
app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(
    body: str,
    message=Context(),  # get access to raw message
):
    ...
