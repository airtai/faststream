# Access to Message Information

As you know, **FastStream** serializes a message body and provides you access to it through function arguments. But sometimes you want access to a message_id, headers, or other meta-information.

## Message Access

You can get it in a simple way: just acces to the message object in the [Context](../getting-started/context/existed.md){.internal-link}!

It contains the required information such as:

* `#!python body: bytes`
* `#!python decoded_body: Any`
* `#!python content_type: str`
* `#!python reply_to: str`
* `#!python headers: dict[str, Any]`
* `#!python message_id: str`
* `#!python correlation_id: str`

It is a **FastStream** wrapper around a native broker library message (`nats.aio.msg.Msg` in the *NATS* case), you can access with `raw_message`.

```python hl_lines="1 6"
from faststream.nats.annotations import NatsMessage

@broker.subscriber("test")
async def base_handler(
    body: str,
    msg: NatsMessage,
):
    print(msg.correlation_id)
```

Also, if you can't find the information you reqiure, you can get access directly to the wrapped `nats.aio.msg.Msg`, which contains complete message information.

```python hl_lines="6"
from nats.aio.msg import Msg
from faststream.nats.annotations import NatsMessage

@broker.subscriber("test")
async def base_handler(body: str, msg: NatsMessage):
    raw: Msg = msg.raw_message
    print(raw)
```

## Message Fields Access

But in the most cases, you don't need all message fields; you need to access some of them. You can use [Context Fields access](../getting-started/context/fields.md){.internal-link} feature for this reason.

For example, you can get access to the `correlation_id` like this:

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

{!> includes/message/annotated.md !}