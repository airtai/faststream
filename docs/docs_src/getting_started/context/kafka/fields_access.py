from faststream import Context, FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.message import KafkaMessage

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test-topic")
async def handle(
    msg: KafkaMessage = Context("message"),
    correlation_id: str = Context("message.correlation_id"),
    user_header: str = Context("message.headers.user"),
):
    assert msg.correlation_id == correlation_id
    assert msg.headers["user"] == user_header
