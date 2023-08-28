from types import TracebackType
from typing import Optional, Type

from faststream import BaseMiddleware, FastStream
from faststream.rabbit import RabbitBroker
from faststream.types import DecodedMessage


class TopLevelMiddleware(BaseMiddleware):
    async def on_receive(self) -> None:
        print(f"call toplevel middleware with msg: {self.msg}")
        return await super().on_receive()

    async def after_processed(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> bool:
        print("highlevel middleware out")
        return await super().after_processed(exc_type, exc_val, exec_tb)


class HandlerMiddleware(BaseMiddleware):
    async def on_consume(self, msg: DecodedMessage) -> DecodedMessage:
        print(f"call handler middleware with body: {msg}")
        return "fake message"

    async def after_consume(self, err: Optional[Exception]) -> None:
        print("handler middleware out")
        return await super().after_consume(err)


broker = RabbitBroker(
    "amqp://guest:guest@localhost:5672/",
    middlewares=(TopLevelMiddleware,),
)
app = FastStream(broker)


@broker.subscriber("test", middlewares=(HandlerMiddleware,))
async def handle(msg):
    assert msg == "fake message"


@app.after_startup
async def test_publish():
    await broker.publish("message", "test")
