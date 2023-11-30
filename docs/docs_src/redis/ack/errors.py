from faststream import FastStream
from faststream.exceptions import AckMessage
from faststream.redis import RedisBroker

broker = RedisBroker("localhost:6379")
app = FastStream(broker)


@broker.subscriber("test-stream")
async def handle(body):
    processing_logic(body)


def processing_logic(body):
    if True:
        raise AckMessage()


@app.after_startup
async def test_publishing():
    await broker.publish("Hello World!", "test-stream")
