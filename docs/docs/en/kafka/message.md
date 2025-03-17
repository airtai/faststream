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

As you may know, **FastStream** serializes a message body and provides you access to it through function arguments. However, there are times when you need to access additional message attributes such as offsets, headers, or other metadata.

## Message Access

You can easily access this information by referring to the message object in the [Context](../getting-started/context/existed.md)

This object serves as a unified **FastStream** wrapper around the native broker library message (for example, `aiokafka.ConsumerRecord` in the case of *Kafka*). It contains most of the required information, including:

* `#!python body: bytes`
* `#!python checksum: int`
* `#!python headers: Sequence[Tuple[str, bytes]]`
* `#!python key: Optional[aiokafka.structs.KT]`
* `#!python offset: int`
* `#!python partition: int`
* `#!python serialized_key_size: int`
* `#!python serialized_value_size: int`
* `#!python timestamp: int`
* `#!python timestamp_type: int`
* `#!python topic: str`
* `#!python value: Optional[aiokafka.structs.VT]`

For example, if you would like to access the headers of an incoming message, you would do so like this:

```python hl_lines="1 6"
from faststream.kafka import KafkaMessage

@broker.subscriber("test")
async def base_handler(
    body: str,
    msg: KafkaMessage,
):
    print(msg.headers)
```

## Message Fields Access

In most cases, you don't need all message fields; you need to know just a part of them.
You can use [Context Fields access](../getting-started/context/fields.md) feature for this.

For example, you can get access to the `headers` like this:

```python hl_lines="6"
from faststream import Context

@broker.subscriber("test")
async def base_handler(
    body: str,
    headers: str = Context("message.headers"),
):
    print(headers)
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
