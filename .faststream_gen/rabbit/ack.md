# Consuming Acknowledgements

As you may know, *RabbitMQ* employs a rather extensive [Acknowledgement](https://www.rabbitmq.com/confirms.html){.external-link target="_blank"} policy.

In most cases, **FastStream** automatically acknowledges (*acks*) messages on your behalf. When your function executes correctly, including sending all responses, a message will be acknowledged (and rejected in case of an exception).

However, there are situations where you might want to use a different acknowledgement logic.

## Retries

If you prefer to use a *nack* instead of a *reject* when there's an error in message processing, you can specify the `retry` flag in the `#!python  @broker.subscriber(...)` method, which is responsible for error handling logic.

By default, this flag is set to `False`, indicating that if an error occurs during message processing, the message can still be retrieved from the queue:

```python
@broker.subscriber("test", retry=False) # don't handle exceptions
async def base_handler(body: str):
    ...
```

If this flag is set to `True`, the message will be *nack*ed and placed back in the queue each time an error occurs. In this scenario, the message can be processed by another consumer (if there are several of them) or by the same one:

```python
@broker.subscriber("test", retry=True)  # try again indefinitely
async def base_handler(body: str):
    ...
```

If the `retry` flag is set to `int`, the message will be placed back in the queue and the number of retries will be limited to this number:

```python
@broker.subscriber("test", retry=3)     # make up to 3 attempts
async def base_handler(body: str):
    ...
```

!!! bug
    At the moment, attempts are counted only by the current consumer. If the message goes to another consumer, it will have its own counter.
    Subsequently, this logic will be reworked.

!!! tip
    For more complex error handling cases you can use [tenacity](https://tenacity.readthedocs.io/en/latest/){.external-link target="_blank"}

## Manual Ack

If you want to *ack* message manually, you can get access directy to the message object via the [Context](../getting-started/context/existed.md){.internal-link} and call the method.

```python
from faststream.rabbit import RabbitMessage

@broker.subscriber("test")
async def base_handler(body: str, msg: RabbitMessage):
    await msg.ack()
    # or
    await msg.nack()
    # or
    await msg.reject()
```

**FastStream** will see that the message was already *ack*ed and will do nothing at process end.

## Interrupt Process

If you want to interrupt message processing at any callstack, you can raise `faststream.exceptions.AckMessage`

``` python linenums="1" hl_lines="16"
from faststream import FastStream
from faststream.exceptions import AckMessage
from faststream.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)


@broker.subscriber("test-queue")
async def handle(body):
    smth_processing(body)


def smth_processing(body):
    if True:
        raise AckMessage()


@app.after_startup
async def test_publishing():
    await broker.publish("Hello!", "test-queue")
```

This way **FastStream** interrupts the current message proccessing and *ack* it immediately. Also, you can raise `NackMessage` and `RejectMessage` too.
