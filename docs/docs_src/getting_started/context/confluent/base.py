from faststream import Context, FastStream
from faststream.confluent import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(
    body: str,
    message=Context(),  # get access to raw message
):
    ...
