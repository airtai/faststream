# RabbitMQ Streams

*RabbitMQ* has a [Streams](https://www.rabbitmq.com/streams.html){.exteranl-link target="_blank"} feature, pretty close to *Kafka* topics.

The main difference from regular *RabbitMQ* queues - messages are not deletes after consuming.

And **FastStream** supports this prefect feature as well!

```python linenums="1" hl_lines="4 10-12 17"
from faststream import FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitQueue

broker = RabbitBroker(max_consumers=10)
app = FastStream(broker)

queue = RabbitQueue(
    name="test",
    durable=True,
    arguments={
        "x-queue-type": "stream",
    },
)


@broker.subscriber(
    queue,
    consume_arguments={"x-stream-offset": "first"},
)
async def handle(msg, logger: Logger):
    logger.info(msg)


@app.after_startup
async def test():
    await broker.publish("Hi!", queue)
```
