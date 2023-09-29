# Publishing

**FastStream** `NatsBroker` supports all regular [publishing usecases](../../getting-started/publishing/index.md){.internal-link}. you can use them without any changes.

However, if you wish to further customize the publishing logic further, you should take a more deep-dive look at specific RabbitBroker parameters.

## NATS Publishing

`NatsBroker` also uses the unified `publish` method (from a `publisher` object) to send messages.

``` python
import asyncio
from faststream.nats import NatsBroker

async def pub():
    async with NatsBroker() as broker:
        await broker.publish(
            "Hi!",
            subject="test",
        )

asyncio.run(pub())
```

## Basic arguments

The `publish` method accepts the following arguments:

* `#!python message = ""` - message to send
* `#!python subject: str` - *subject*, where the message will be sent.

## Message Parameters

* `#!python headers: dict[str, str] | None = None` - headers of the message being sent (used by consumers)
* `#!python correlation_id: str | None = None` - message id, which helps to match the original message with the reply to it (generated automatically)

## NatsJS Parameters

* `#!python stream: str | None = None` - validate that subject is in stream
* `#!python timeout: float | None = None` - wait for NATS server response
