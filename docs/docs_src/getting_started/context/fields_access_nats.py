from faststream import Context, FastStream
from faststream.nats import NatsBroker
from faststream.nats.message import NatsMessage

broker = NatsBroker("nats://localhost:4222")
app = FastStream(broker)


@broker.subscriber("test-subject")
async def handle(
    msg: NatsMessage = Context("message"),
    correlation_id: str = Context("message.correlation_id"),
    user_header: str = Context("message.headers.user"),
):
    assert msg.correlation_id == correlation_id
    assert msg.headers["user"] == user_header
