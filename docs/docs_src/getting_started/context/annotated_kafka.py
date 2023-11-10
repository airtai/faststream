from typing import Annotated

from faststream import Context, FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.message import KafkaMessage

Message = Annotated[KafkaMessage, Context()]

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(
    body: str,
    message: Message,  # get access to raw message
):
    ...
