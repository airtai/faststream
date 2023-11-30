from faststream import Context, FastStream
from faststream.nats import NatsBroker

broker = NatsBroker("nats://localhost:4222")
app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(
    body: str,
    message=Context(),  # get access to raw message
):
    ...
