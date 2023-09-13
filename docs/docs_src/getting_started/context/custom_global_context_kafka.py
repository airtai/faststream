from faststream import FastStream, ContextRepo, Context
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("test-topic")
async def handle(
    msg: str,
    secret: str=Context(),
):
    assert secret == "my-perfect-secret"


@app.on_startup
async def set_global(context: ContextRepo):
    context.set_global("secret", "my-perfect-secret")

