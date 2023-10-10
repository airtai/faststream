from faststream import Context, FastStream
from faststream.rabbit import RabbitBroker
from faststream.rabbit.message import RabbitMessage

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)


@broker.subscriber("test-queue")
async def handle(
    msg: RabbitMessage = Context("message"),
    correlation_id: str = Context("message.correlation_id"),
):
    assert msg.correlation_id == correlation_id
