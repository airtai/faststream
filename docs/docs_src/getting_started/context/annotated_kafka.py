from typing import Annotated

from faststream import Context, FastStream
from faststream.kafka import KafkaBroker, KafkaMessage

Message = Annotated[KafkaMessage, Context()]

broker = KafkaBroker()
app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(
    body: str,
    message: Message,  # get access to raw message
):
    ...
