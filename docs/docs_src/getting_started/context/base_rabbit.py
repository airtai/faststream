from faststream import Context, FastStream
from faststream.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(
    body: str,
    message=Context(),  # get access to raw message
):
    ...
