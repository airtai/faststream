# Middlewares

**Middlewares** are a powerful mechanism that allows you to add additional logic to any stage of the message processing pipeline.

This way, you can greatly extend your **FastStream** application with features such as:

* Integration with any logging/metrics systems
* Application-level message serialization logic
* Rich publishing of messages with extra information
* And many other capabilities

**Middlewares** have several methods to override. You can implement some or all of them and use middlewares at the broker, router, or subscriber level. Thus, middlewares are the most flexible  **FastStream** feature.

## Message Receive Wrapper

Unfortunately, this powerful feature has a somewhat complex signature too.

Using middlewares, you can wrap the entire message processing pipeline. In this case, you need to specify `on_receive` and `after_processed` methods:

``` python
from faststream import BaseMiddleware

class MyMiddleware(BaseMiddleware):
    async def on_receive(self):
        print(f"Received: {self.message}")
        return await super().on_receive()

    async def after_processed(self, exc_type, exc_val, exec_tb):
        return await super().after_processed(exc_type, exc_val, exec_tb)
```

These methods should be overwritten only in a broker-level middlewares.

```python
Broker(middlewares=[MyMiddleware])
```

In other cases, `on_receive` will be called at every subscriber filter function call.

!!! tip
    Please always call `#!python super()` methods at the end of your function; this is important for correct error processing.

## Message Consuming Wrapper

Also, using middlewares, you are able to wrap consumer function calls directly.

In this case, you need to specify `on_receive` and `after_processed` methods:

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

This way, you can patch the incoming message body right before passing it to your consumer subscriber.

Also, if you have multiple filters for one subscriber, these methods will be called at once when the filtering is completed successfully.

## Message Publishing Wrapper

Finally, using middlewares, you are able to patch outgoing messages too. For example, you can compress/encode outgoing messages at the application level.

In this, case you need to specify `on_publish` and `after_publish` methods:

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
