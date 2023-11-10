from faststream import FastStream
from faststream.redis import RedisBroker, RedisRouter, RedisRoute

broker = RedisBroker("redis://localhost:6379")
app = FastStream(broker)


async def handle(name: str, user_id: int):
    assert name == "John"
    assert user_id == 1


router = RedisRouter(handlers=(RedisRoute(handle, "test-channel"),))

broker.include_router(router)


@app.after_startup
async def test():
    await broker.publish({"name": "John", "user_id": 1}, channel="test-channel")
