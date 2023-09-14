# RabbitMQ Queue/Exchange Declaration

**FastStream** declares and validates all using by *publishers* and *subscribers* *RabbitMQ* objects manually, but sometimes you need to declare not-using object manually.

This reason **RabbitBroker** provides you a methods to make it easely.

``` python linenums="1" hl_lines="15-20 22-27"
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
    await broker.declare_exchange(
        RabbitExchange(
            name="some-exchange",
            type=ExchangeType.FANOUT,
        )
    )

    await broker.declare_queue(
        RabbitQueue(
            name="some-queue",
            durable=True,
        )
    )
```

These methods require just a one argument (`RabbitQueue`/`RabbitExchange`) containing information about your *RabbitMQ* required objects. They are declare/validates *RabbitMQ* objects and returns you low-level **aio-pika** robust objects to interact with.

!!! tip
    Also, these methods are indempotence, so you can call them with the same arguments multiple times, but the objects will creates just at once, next times the method will return already stored in memory object. This way you can get access to any queue/exchange created automatically.
