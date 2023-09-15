from faststream import FastStream, ContextRepo, Context
from faststream.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)


@broker.subscriber("test-queue")
async def handle(
    msg: str,
    secret: str=Context(),
):
    assert secret == "my-perfect-secret" # pragma: allowlist secret


@app.on_startup
async def set_global(context: ContextRepo):
    context.set_global("secret", "my-perfect-secret")
