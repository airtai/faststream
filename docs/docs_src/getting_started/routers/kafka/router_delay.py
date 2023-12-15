from faststream import FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka import KafkaRoute, KafkaRouter

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


async def handle(name: str, user_id: int):
    assert name == "John"
    assert user_id == 1


router = KafkaRouter(
    handlers=(
        KafkaRoute(handle, "test-topic"),
    )
)

broker.include_router(router)


@app.after_startup
async def test():
    await broker.publish({"name": "John", "user_id": 1}, topic="test-topic")
