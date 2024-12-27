from faststream import FastStream
from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
)

broker = RabbitBroker()
app = FastStream(broker)


@app.after_startup
async def declare_smth():
    queue = RabbitQueue(
        name="some-queue",
        durable=True,
    )

    exchange = RabbitExchange(
        name="some-exchange",
        type=ExchangeType.FANOUT,
    )

    await broker.declare_binding(
        queue=queue,
        exchange=exchange,
        routing_key=queue.name # This parameter is optional
    )
