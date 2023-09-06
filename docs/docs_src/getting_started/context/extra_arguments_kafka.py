from faststream import Context, FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.annotations import ContextRepo

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test-topic")
async def handle(
    secret: int = Context("secret_int"),
    casted_secret: int = Context("secret_int", cast=True),
    not_existed: None = Context("not_existed", default=None),
):
    assert secret == "1"
    assert casted_secret == 1
    assert not_existed is None


@app.after_startup
async def test(context: ContextRepo):
    context.set_global("secret_int", "1")
    await broker.publish("", "test-topic")
