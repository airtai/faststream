---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Access to Message Information

As you know, **FastStream** serializes a message body and provides you access to it through function arguments. But sometimes you need access to a message_id, headers, or other meta-information.

## Message Access

You can get it in a simple way: just access the message object in the [Context](../getting-started/context/existed.md){.internal-link}.

This message contains the required information such as:

* `#!python body: bytes`
* `#!python decoded_body: Any`
* `#!python content_type: str`
* `#!python reply_to: str`
* `#!python headers: dict[str, Any]`
* `#!python path: dict[str, Any]`
* `#!python message_id: str`
* `#!python correlation_id: str`


Also, it is a **FastStream** wrapper around a native broker library message (`aio_pika.IncomingMessage` in the *RabbitMQ* case) that you can access with `raw_message`.

```python hl_lines="1 6"
from faststream.rabbit import RabbitMessage

@broker.subscriber("test")
async def base_handler(
    body: str,
    msg: RabbitMessage,
):
    print(msg.correlation_id)
```

Also, if you can't find the information you require, you can get access directly to the wrapped `aio_pika.IncomingMessage`, which contains complete message information.

```python hl_lines="6"
from aio_pika import IncomingMessage
from faststream.rabbit import RabbitMessage

@broker.subscriber("test")
async def base_handler(body: str, msg: RabbitMessage):
    raw: IncomingMessage = msg.raw_message
    print(raw)
```

## Message Fields Access

But in most cases, you don't need all message fields; you need to access some of them. You can use [Context Fields access](../getting-started/context/fields.md){.internal-link} feature for this reason.

For example, you can access the `correlation_id` like this:

```python hl_lines="6"
from faststream import Context

@broker.subscriber("test")
async def base_handler(
    body: str,
    cor_id: str = Context("message.correlation_id"),
):
    print(cor_id)
```

Or even directly from the raw message:

```python hl_lines="6"
from faststream import Context

@broker.subscriber("test")
async def base_handler(
    body: str,
    cor_id: str = Context("message.raw_message.correlation_id"),
):
    print(cor_id)
```

But this code is too long to be reused everywhere. In this case, you can use a Python [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated){.external-link target="_blank"} feature:

=== "python 3.9+"
    ```python hl_lines="4 9"
    from types import Annotated
    from faststream import Context

    CorrelationId = Annotated[str, Context("message.correlation_id")]

    @broker.subscriber("test")
    async def base_handler(
        body: str,
        cor_id: CorrelationId,
    ):
        print(cor_id)
    ```

=== "python 3.6+"
    ```python hl_lines="4 9"
    from typing_extensions import Annotated
    from faststream import Context

    CorrelationId = Annotated[str, Context("message.correlation_id")]

    @broker.subscriber("test")
    async def base_handler(
        body: str,
        cor_id: CorrelationId,
    ):
        print(cor_id)
    ```


## Headers Access

Sure, you can get access to a raw message and get the headers dict itself, but more often you just need a single header field. So, you can easily access it using the `Context`:

```python hl_lines="6"
from faststream import Context

@broker.subscriber("test")
async def base_handler(
    body: str,
    user: str = Context("message.headers.user"),
):
    ...
```

Using the special `Header` class is more convenient, as it also validates the header value using Pydantic. It works the same way as `Context`, but it is just a shortcut to `Context` with a default setup. So, you already know how to use it:

```python hl_lines="6"
from faststream import Header

@broker.subscriber("test")
async def base_handler(
    body: str,
    user: str = Header(),
):
    ...
```


## Topic Pattern Access

As you know, **Rabbit** allows you to use a pattern like this `#!python "logs.*"` with a [Topic](./examples/topic.md){.internal-link} exchange. Getting access to the real `*` value is an often-used scenario and **FastStream** provide it to you with the `Path` object (which is a shortcut to `#!python Context("message.path.*")`).

To use it, you just need to replace your `*` with `{variable-name}` and use `Path` as a regular `Context` object:

```python hl_lines="7 11 16"
from faststream import Path
from faststream import RabbitQueue, RabbitExchane, ExchangeType

@broker.subscriber(
    RabbitQueue(
        "test-queue",
        routing_key="logs.{level}",
    ),
    RabbitExchange(
        "test-exchange",
        type=ExchangeType.TOPIC,
    )
)
async def base_handler(
    body: str,
    level: str = Path(),
):
    ...
```
