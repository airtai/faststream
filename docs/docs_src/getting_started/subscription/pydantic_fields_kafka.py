from pydantic import Field, NonNegativeInt

from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test-topic")
async def handle(
    name: str = Field(..., examples=["john"], description="Registered user name"),
    user_id: NonNegativeInt = Field(
        ..., examples=[1], description="Registered user id"
    ),
):
    assert name == "john"
    assert user_id == 1


@app.after_startup
async def test():
    await broker.publish({"name": "john", "user_id": 1}, topic="test-topic")
