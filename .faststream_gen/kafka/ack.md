# Consuming Acknowledgements

As you may know, *Kafka* consumer should commit a topic offset at message consuming.

By default, **FastStream** automatically commit (*acks*) topic offset on message consumption. This is the *at most once* consuming strategy.

But, if you want to use *at least once* strategy, you should commit offset *AFTER* the message processed correctly. This reason you should set a consumer group and disable `auto_commit` option:

```python
@broker.subscriber(
    "test", group_id="group", auto_commit=False
)
async def base_handler(body: str):
    ...
```

This way, when your function executes correctly, including sending all responses, a message will be acknowledged (and do nothing in case of an exception).

However, there are situations where you might want to use different acknowledgement logic.

## Manual Acknowledgement

If you want to acknowledge a message manually, you can get access directy to the message object via the [Context](../getting-started/context/existed.md){.internal-link} and call the method.

```python
from faststream.kafka.annotations import KafkaMessage

@broker.subscriber(
    "test", group_id="group", auto_commit=False
)
async def base_handler(body: str, msg: KafkaMessage):
    await msg.ack()
    # or
    await msg.nack()
```

!!! tip
    Using `nack` you prevent offset commit and the message can be consumed by another consumer with the same group.

**FastStream** will see that the message was already acknowledged and will do nothing at the end of the process.

## Interrupt Process

If you want to interrupt message processing at any call stack, you can raise `faststream.exceptions.AckMessage`

``` python linenums="1" hl_lines="2 18"
from faststream import FastStream
from faststream.exceptions import AckMessage
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber(
    "test-topic", group_id="test-group", auto_commit=False
)
async def handle(body):
    smth_processing(body)


def smth_processing(body):
    if True:
        raise AckMessage()


@app.after_startup
async def test_publishing():
    await broker.publish("Hello!", "test-topic")
```

This way, **FastStream** interrupts the current message proccessing and acknowledges it immediately. Also, you can raise `NackMessage` as well.
