# Access to Message information

As you know, **FastStream** serializes a message body and provides you access to it by function arguments. But sometimes you want to access a message offset, headers or other meta information.

## Message access

You can get it in a simple way too: just acces to the message object in the [Context](../getting-started/context/existed.md)!

It is an unified **FastStream** wrapper around native broker library message (`aiokafka.ConsumerRecord` in the *Kafka* case). It contains most part of required information like:

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

## Message Fields access

But in the most cases you don't need all message fields, you need to know just one of them. You can use [Context Fields access](../getting-started/context/fields.md) feature for this reason.

Like an example, you can get access to the `headers` like this:

```python hl_lines="6"
from faststream import Context

@broker.subscriber("test")
async def base_handler(
    body: str,
    headers: str = Context("message.headers"),
):
    print(headers)
```