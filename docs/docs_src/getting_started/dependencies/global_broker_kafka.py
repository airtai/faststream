from faststream import Depends, FastStream
from faststream.kafka import KafkaBroker


async def validate_user(name: str, user_id: int):
    """Emulate DB request"""
    user = {
        "name": "john",
        "user_id": user_id,
    }

    if user["name"] != name:
        raise ValueError()


broker = KafkaBroker("localhost:9092", dependencies=(Depends(validate_user),))
app = FastStream(broker)


@broker.subscriber("test-topic")
async def handle(name: str):
    assert name == "john"


@app.after_startup
async def test():
    await broker.publish({"name": "john", "user_id": 1}, topic="test-topic")
