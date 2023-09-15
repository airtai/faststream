# Annotation Serialization

## Basic usage

As you already know, **FastStream** serialize your incoming message body in according to the function type annotations using [**Pydantic**](https://docs.pydantic.dev){.external-link target="_blank"}.

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

As an other Python primitive types too (`#!python float`, `#!python bool`, `#!python datetime`, etc)

!!! note
    If incoming message can not be serialized by described schema, **FastStream** raises `pydantic.ValidationError` with correct log message.

Also, thanks to **Pydantic** (again), **FastStream** is able to serialize (and validates) more complex types like `pydantic.HttpUrl`, `pydantic.PostitiveInt`, etc.

## JSON Basic serialization

But how we can serialize more complex message, like `#!json { "name": "John", "user_id": 1 }` ?

For sure, we can serialize it as a simple `#!python dict`

```python
from typing import Dict, Any

@broker.subscriber("test")
async def handle(msg: dict[str, Any]):
    ...
```

But it doesn't look like a correct message validation, isn't it?

This reason **FastStream** supports per-argument message serialization: you can declare multiple arguments with various types and your message will unpack to them:

=== "Kafka"
    ```python
    {!> docs_src/getting_started/subscription/annotation_kafka.py [ln:8-11] !}
    ```

=== "RabbitMQ"
    ```python
    {!> docs_src/getting_started/subscription/annotation_rabbit.py [ln:8-11] !}
    ```
