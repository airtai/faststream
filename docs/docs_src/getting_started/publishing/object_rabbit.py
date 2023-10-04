from faststream import FastStream
from faststream.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)

publisher = broker.publisher("another-queue")

@publisher
@broker.subscriber("test-queue")
async def handle() -> str:
    return "Hi!"


@broker.subscriber("another-queue")
async def handle_next(msg: str):
    assert msg == "Hi!"
