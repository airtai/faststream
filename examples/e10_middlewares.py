from contextlib import asynccontextmanager

from propan import PropanApp
from propan.rabbit import RabbitBroker, RabbitMessage


@asynccontextmanager
async def highlevel_middleware(message: RabbitMessage):
    print("highlevel middleware in")
    yield
    print("highlevel middleware out")


@asynccontextmanager
async def handler_middleware(message: RabbitMessage):
    print("handler middleware in")
    message.decoded_body = "fake message"
    yield
    print("handler middleware out")


broker = RabbitBroker(
    "amqp://guest:guest@localhost:5672/",
    middlewares=(highlevel_middleware,),
)
app = PropanApp(broker)


@broker.subscriber("test", middlewares=(handler_middleware,))
async def handle(msg):
    assert msg == "fake message"


@app.after_startup
async def test_publish():
    await broker.publish("message", "test")
