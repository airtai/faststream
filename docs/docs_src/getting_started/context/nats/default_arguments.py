from faststream import Context, FastStream
from faststream.nats import NatsBroker

broker = NatsBroker("nats://localhost:4222")
app = FastStream(broker)

@broker.subscriber("test-subject")
async def handle(
    not_existed: None = Context("not_existed", default=None),
):
    assert not_existed is None
