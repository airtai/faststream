---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Annotation Serialization

## Basic usage

As you already know, **FastStream** serializes your incoming message body according to the function type annotations using [**Pydantic**](https://docs.pydantic.dev){.external-link target="_blank"}.

So, there are some valid usecases:

{! includes/getting_started/subscription/annotation/1.md !}

As with other Python primitive types as well (`#!python float`, `#!python bool`, `#!python datetime`, etc)

!!! note
    If the incoming message cannot be serialized by the described schema, **FastStream** raises a `pydantic.ValidationError` with a correct log message.

Also, thanks to **Pydantic** (again), **FastStream** is able to serialize (and validate) more complex types like `pydantic.HttpUrl`, `pydantic.PostitiveInt`, etc.

## JSON Basic Serialization

But how can we serialize more complex message, like `#!json { "name": "John", "user_id": 1 }` ?

For sure, we can serialize it as a simple `#!python dict`

{! includes/getting_started/subscription/annotation/2.md !}

But it doesn't looks like a correct message validation, does it?

For this reason, **FastStream** supports per-argument message serialization: you can declare multiple arguments with various types and your message will unpack to them:

{! includes/getting_started/subscription/annotation/3.md !}

!!! tip
  By default **FastStream** uses `json.loads` to decode and `json.dumps` to encode your messages. But if you prefer [**orjson**](https://github.com/ijl/orjson){.external-link target="_blank"}, just install it and framework will use it automatically.
