from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test-topic")
async def handle(name: str, user_id: int):
    assert name == "john"
    assert user_id == 1


@app.after_startup
async def test():
    await broker.publish({"name": "john", "user_id": 1}, topic="test-topic")
