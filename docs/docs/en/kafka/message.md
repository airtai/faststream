# Access to Message information

As you know, **FastStream** serializes a message body and provides you access to it by function arguments. But sometimes you want to access to message_id, headers or other meta information.

## Message access

You can get it in a simple way too: just acces to the message object in the [Context](../getting-started/context/existed.md){.internal-link}!

It is an unified **FastStream** wrapper around native broker library message (`aiokafka.ConsumerRecord` in the *Kafka* case). It contains most part of required information like:

* `#!python body: bytes`
* `#!python decoded_body: Any`
* `#!python content_type: str`
* `#!python reply_to: str`
* `#!python headers: dict[str, Any]`
* `#!python message_id: str`
* `#!python correlation_id: str`

```python hl_lines="1 6"
from faststream.kafka import KafkaMessage

@broker.subscriber("test")
async def base_handler(
    body: str,
    msg: KafkaMessage,
):
    print(msg.correlation_id)
```

Also, if you doesn't find information you reqiure, you can get access right to the wrapped `aiokafka.ConsumerRecord`, contains total message information.

```python hl_lines="6"
from aiokafka import ConsumerRecord
from faststream.kafka import KafkaMessage

@broker.subscriber("test")
async def base_handler(body: str, msg: KafkaMessage):
    raw: ConsumerRecord = msg.raw_message
    print(raw)
```

## Message Fields access

But in the most cases you don't need all message fields, you need to know just one of them. You can use [Context Fields access](../getting-started/context/fields.md){.internal-link} feature for this reason.

Like an example, you can get access to the `correlation_id` like this:

```python hl_lines="6"
from faststream import Context

@broker.subscriber("test")
async def base_handler(
    body: str,
    cor_id: bytes = Context("message.correlation_id"),
):
    print(cor_id)
```

Or even directly to the raw message partition key:

```python hl_lines="6"
from faststream import Context

@broker.subscriber("test")
async def base_handler(
    body: str,
    key: bytes | None = Context("message.raw_message.key"),
):
    print(key)
```

But this code is a too long to reuse it everywhere. Thus, you can use python [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated){.external-link target="_blank"} feature:


=== "python 3.9+"
    ```python hl_lines="4 9"
    from types import Annotated
    from faststream import Context

    PartitionKey = Annotated[bytes | None, Context("message.raw_message.key")]

    @broker.subscriber("test")
    async def base_handler(
        body: str,
        key: PartitionKey,
    ):
        print(key)
    ```

=== "python 3.6+"
    ```python hl_lines="4 9"
    from typing_extensions import Annotated
    from faststream import Context

    PartitionKey = Annotated[bytes | None, Context("message.raw_message.key")]

    @broker.subscriber("test")
    async def base_handler(
        body: str,
        key: PartitionKey,
    ):
        print(key)
    ```
