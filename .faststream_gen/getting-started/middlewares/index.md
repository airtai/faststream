# Middlewares

**Middlewares** - is a powerfull mechanizm allows you to add extra logic to any message processing pipeline stage.

This way you can extreamly extend your **FastStream** application by features:

* integrate with any logging/metrics systems
* application-level message serialization logic
* rich publishing messages with extra information
* and many other stuff

**Middlewares** has a several methods to overwride. You can implement some or all of them, use middlewares at broker, router or subscriber level. Thus middlewares is a most flexible **FastStream** feature.

## Message receive wrapper

Unfortunatelly, powerfull feature has a pretty complex signature too.

Using middlewares you can wrap total message processing pipeline. In this case you need to specify `on_receive` and `after_processed` methods:

``` python
from faststream import BaseMiddleware:

class MyMiddleware(BaseMiddleware):
    async def on_receive(self):
        print(f"Received: {self.message}")
        return await super().on_receive()

    async def after_processed(self, exc_type, exc_val, exec_tb):
        return await super().after_processed(exc_type, exc_val, exec_tb)
```

These methods should be overwritten only in a Broker-level middlewares.

```python
Broker(middlewares=[MyMiddleware])
```

In the other cases `on_receive` will be called at every subscriber filter function calling.

!!! tip
    Please, always call `#!python super()` methods at the end of your function - this is important for correct errors processing

## Message consuming wrapper

Also, using middlewares you are able to wrap consumer function calling directly.

In this case you need to specify `on_receive` and `after_processed` methods:

``` python
from typing import Optional

from faststream import BaseMiddleware:
from faststream.types import DecodedMessage

class MyMiddleware(BaseMiddleware):
    async def on_consume(self, msg: DecodedMessage) -> DecodedMessage:
        return await super().on_consume(msg)

    async def after_consume(self, err: Optional[Exception]) -> None:
        return await super().after_consume(err)
```

This way you can patch incoming message body right before passing it to you consumer subscriber.

Also, if you have multiple filters for one subscriber, these methods will be called at once: then the filtering complete success.

## Message publishing wrapper

Finally, using middlewares you are able to patch outcoming message too. This way, (as an example) you can compress/encode outcoming message at Application level.

In this case you need to specify `on_publish` and `after_publish` methods:

``` python
from typing import Optional

from faststream import BaseMiddleware:
from faststream.types import SendableMessage

class MyMiddleware(BaseMiddleware):
    async def on_publish(self, msg: SendableMessage) -> SendableMessage:
        return await super().on_publish(msg)

    async def after_publish(self, err: Optional[Exception]) -> None:
        return await super().after_publish(err)
```
