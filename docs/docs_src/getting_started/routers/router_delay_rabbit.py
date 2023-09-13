from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitRoute, RabbitRouter

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)


async def handle(name: str, user_id: int):
    assert name == "john"
    assert user_id == 1


router = RabbitRouter(handlers=(RabbitRoute(handle, "test-queue"),))

broker.include_router(router)


@app.after_startup
async def test():
    await broker.publish({"name": "john", "user_id": 1}, queue="test-queue")
