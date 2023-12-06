from faststream import Context, FastStream
from faststream.redis import RedisBroker
from faststream.redis.message import RedisMessage

broker = RedisBroker("redis://localhost:6379")
app = FastStream(broker)


@broker.subscriber("test-channel")
async def handle(
    msg: RedisMessage = Context("message"),
    correlation_id: str = Context("message.correlation_id"),
    user_header: str = Context("message.headers.user"),
):
    assert msg.correlation_id == correlation_id
    assert msg.headers["user"] == user_header
