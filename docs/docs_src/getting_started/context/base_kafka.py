from faststream import Context, FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker()
app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(
    body: str,
    message=Context(),  # get access to raw message
):
    ...
