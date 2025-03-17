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

As you may know, *Nats* employs a rather extensive [Acknowledgement](https://docs.nats.io/using-nats/developer/develop_jetstream#acknowledging-messages){.external-link target="_blank"} policy.

In most cases, **FastStream** automatically acknowledges (*acks*) messages on your behalf. When your function executes correctly, including sending all responses, a message will be acknowledged (and rejected in case of an exception).

However, there are situations where you might want to use different acknowledgement logic.

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

!!! tip
    For more complex error handling cases, you can use [tenacity](https://tenacity.readthedocs.io/en/latest/){.external-link target="_blank"}

## Manual Acknowledgement

If you want to acknowledge a message manually, you can get access directly to the message object via the [Context](../../getting-started/context/existed.md){.internal-link} and call the method.

```python
from faststream.nats.annotations import NatsMessage

@broker.subscriber("test")
async def base_handler(body: str, msg: NatsMessage):
    await msg.ack()
    # or
    await msg.nack()
    # or
    await msg.reject()
```

**FastStream** will see that the message was already acknowledged and will do nothing at the end of the process.

## Interrupt Process

If you want to interrupt message processing at any call stack, you can raise `faststream.exceptions.AckMessage`

```python linenums="1" hl_lines="2 16"
{! docs_src/nats/ack/errors.py !}
```

This way, **FastStream** interrupts the current message processing and acknowledges it immediately. Also, you can raise `NackMessage` and `RejectMessage` too.

!!! tip
    If you want to disable **FastStream** Acknowledgement logic at all, you can use
    `#!python @broker.subscriber(..., no_ack=True)` option. This way you should always process a message (ack/nack/terminate/etc) by yourself.

