from faststream import Context, FastStream
from faststream.nats import NatsBroker, NatsMessage

broker = NatsBroker("nats://localhost:4222")
app = FastStream(broker)


@broker.subscriber("test-subject")
async def handle(
    msg: NatsMessage = Context("message"),
    correlation_id: str = Context("message.correlation_id"),
):
    assert msg.correlation_id == correlation_id
