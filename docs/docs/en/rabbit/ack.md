---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

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

If the `retry` flag is set to an `int`, the message will be placed back in the queue, and the number of retries will be limited to this number:

```python
@broker.subscriber("test", retry=3)     # make up to 3 attempts
async def base_handler(body: str):
    ...
```

!!! tip
    **FastStream** identifies the message by its `message_id`. To make this option work, you should manually set this field on the producer side (if your library doesn't set it automatically).

!!! bug
    At the moment, attempts are counted only by the current consumer. If the message goes to another consumer, it will have its own counter.
    Subsequently, this logic will be reworked.

!!! tip
    For more complex error handling cases, you can use [tenacity](https://tenacity.readthedocs.io/en/latest/){.external-link target="_blank"}

## Manual acknowledgement

If you want to acknowledge a message manually, you can get access directly to the message object via the [Context](../getting-started/context/existed.md){.internal-link} and call the method.

```python
from faststream.rabbit.annotations import RabbitMessage

@broker.subscriber("test")
async def base_handler(body: str, msg: RabbitMessage):
    await msg.ack()
    # or
    await msg.nack()
    # or
    await msg.reject()
```

**FastStream** will see that the message was already acknowledged and will do nothing at process end.

## Interrupt Process

If you want to interrupt message processing at any call stack, you can raise `faststream.exceptions.AckMessage`

```python linenums="1" hl_lines="2 16"
{! docs_src/rabbit/ack/errors.py !}
```

This way, **FastStream** interrupts the current message processing and acknowledges it immediately. Also, you can raise `NackMessage` and `RejectMessage` too.

!!! tip
    If you want to disable **FastStream** Acknowledgement logic at all, you can use
    `#!python @broker.subscriber(..., no_ack=True)` option. This way you should always process a message (ack/nack/terminate/etc) by yourself.

