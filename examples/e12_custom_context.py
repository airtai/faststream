from typing import TYPE_CHECKING, Any

from typing_extensions import Annotated

from faststream import BaseMiddleware, Context, FastStream, context
from faststream.rabbit import RabbitBroker

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage


class User:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.user_id == other.user_id

    def __ne__(self, other):
        return not self.__eq__(other)


class AuthenticationMiddleware(BaseMiddleware):
    async def on_consume(
        self,
        msg: "StreamMessage[Any]",
    ) -> "StreamMessage[Any]":
        context.set_local("user", User(user_id=1))
        return await super().on_consume(msg)


broker1 = RabbitBroker(middlewares=(AuthenticationMiddleware,))
app1 = FastStream(broker1)


@broker1.subscriber("test-queue")
async def handle1(
    msg,
    user: Annotated[User, Context("user")],
):
    assert msg == "message"
    assert isinstance(user, User)
    assert user == User(user_id=1)


@app1.after_startup
async def test_publish1():
    await broker1.publish("message", "test-queue")


broker2 = RabbitBroker()
app2 = FastStream(broker2)


@broker2.subscriber("test-queue")
async def handle2(
    msg,
    user: Annotated[User, Context("user", default=User(user_id=2))],
):
    assert msg == "message"
    assert isinstance(user, User)
    assert user == User(user_id=2)


@app2.after_startup
async def test_publish2():
    await broker2.publish("message", "test-queue")
