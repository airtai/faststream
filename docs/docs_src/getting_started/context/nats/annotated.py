from typing import Annotated

from faststream import Context, FastStream
from faststream.nats import NatsBroker
from faststream.nats.message import NatsMessage

Message = Annotated[NatsMessage, Context()]

broker = NatsBroker("nats://localhost:4222")
app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(
    body: str,
    message: Message,  # get access to raw message
):
    ...
