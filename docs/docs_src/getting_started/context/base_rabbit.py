from faststream import Context, FastStream
from faststream.rabbit import RabbitBroker

broker = RabbitBroker()
app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(
    body: str,
    message=Context(),  # get access to raw message
):
    ...
