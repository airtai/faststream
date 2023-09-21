# Annotation Serialization

## Basic usage

As you already know, **FastStream** serializes your incoming message body according to the function type annotations using [**Pydantic**](https://docs.pydantic.dev){.external-link target="_blank"}.

So, there are some valid usecases:

```python
@broker.subscriber("test")
async def handle(msg: str):
    ...

@broker.subscriber("test")
async def handle(msg: bytes):
    ...

@broker.subscriber("test")
async def handle(msg: int):
    ...
```

As with other Python primitive types as well (`#!python float`, `#!python bool`, `#!python datetime`, etc)

!!! note
    If the incoming message cannot be serialized by the described schema, **FastStream** raises a `pydantic.ValidationError` with a correct log message.

Also, thanks to **Pydantic** (again), **FastStream** is able to serialize (and validate) more complex types like `pydantic.HttpUrl`, `pydantic.PostitiveInt`, etc.

## JSON Basic Serialization

But how can we serialize more complex message, like `#!json { "name": "John", "user_id": 1 }` ?

For sure, we can serialize it as a simple `#!python dict`

```python
from typing import Dict, Any

@broker.subscriber("test")
async def handle(msg: dict[str, Any]):
    ...
```

But it doesn't looks like a correct message validation, does it?

For this reason, **FastStream** supports per-argument message serialization: you can declare multiple arguments with various types and your message will unpack to them:

=== "Kafka"
    ```python
    {!> docs_src/getting_started/subscription/annotation_kafka.py [ln:8-11] !}
    ```

=== "RabbitMQ"
    ```python
    {!> docs_src/getting_started/subscription/annotation_rabbit.py [ln:8-11] !}
    ```
