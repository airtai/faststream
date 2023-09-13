from faststream import Context, FastStream, apply_types
from faststream.kafka import KafkaBroker
from faststream.kafka.annotations import ContextRepo, KafkaMessage

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test-topic")
async def handle(
    msg: str,
    message: KafkaMessage,
    context: ContextRepo,
    secret=Context(),
):
    with context.scope("correlation_id", message.correlation_id):
        call_a(secret)


@apply_types
def call_a(s, secret=Context()):  # get from call  # get from global context
    assert s == secret
    call_b()


@apply_types
def call_b(
    message: KafkaMessage,  # get from local context
    correlation_id=Context(),  # get from local context
):
    assert correlation_id == message.correlation_id


@app.on_startup
async def set_global(context: ContextRepo):
    context.set_global("secret", "my-perfect-secret")


@app.after_startup
async def test():
    await broker.publish("Hi!", "test-topic")
