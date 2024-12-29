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
async def bind_queue_exchange():
    queue = await broker.declare_queue(
        RabbitQueue(
            name="some-queue",
            durable=True,
        )
    ) # This gives a aio_pika.RobustQueue object

    exchange = await broker.declare_exchange(
        RabbitExchange(
            name="some-exchange",
            type=ExchangeType.FANOUT,
        )
    )   

    await queue.bind(
        queue=queue,
        exchange=exchange,
        routing_key=queue.name # This parameter is optional
    )
