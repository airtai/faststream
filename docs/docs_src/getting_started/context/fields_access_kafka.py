from faststream import Context, FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.annotations import KafkaMessage

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test-topic")
async def handle(
    message: KafkaMessage,
    correlation_id: str = Context("message.correlation_id"),
):
    assert message.correlation_id == correlation_id


@app.after_startup
async def test():
    await broker.publish("", "test-topic")
