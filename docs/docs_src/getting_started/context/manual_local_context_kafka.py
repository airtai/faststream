from faststream import Context, FastStream, apply_types, context
from faststream.kafka import KafkaBroker
from faststream.kafka.annotations import KafkaMessage

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test-topic")
async def handle(
    msg: str,
    message: KafkaMessage,
):
    context.set_local("correlation_id", message.correlation_id)
    call()


@apply_types
def call(
    message: KafkaMessage,
    correlation_id=Context(),
):
    assert correlation_id == message.correlation_id
    context.reset_local("correlation_id")
