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

This object serves as a unified **FastStream** wrapper around the native broker library message (for example, [`confluent_kafka.Message`](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#confluent_kafka.Message) in this case which uses *Confluent* python library). It contains most of the required information, including:

* `#!python headers(): Sequence[Tuple[str, bytes]]`
* `#!python key(): Optional[Union[str, bytes]]`
* `#!python offset(): int`
* `#!python partition(): int`
* `#!python timestamp(): Tuple[int, int]`
* `#!python topic(): str`
* `#!python value(): Optional[Union[str, bytes]]`

For example, if you would like to access the headers of an incoming message, you would do so like this:

```python hl_lines="1 6"
from faststream.confluent import KafkaMessage

@broker.subscriber("test")
async def base_handler(
    body: str,
    msg: KafkaMessage,
):
    print(msg.headers)
```

## Raw Message Access

In some cases, you may want to access the raw `confluent_kafka.Message` created by `confluent_kafka` library. In such cases, you can do so by:

```python hl_lines="1 6"
from faststream.confluent import KafkaMessage

@broker.subscriber("test")
async def base_handler(
    body: str,
    msg: KafkaMessage,
):
    print(msg.raw_message.headers())
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
