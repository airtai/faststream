---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Subscription Basics

**FastStream** provides a Message Broker agnostic way to subscribe to event streams.

You need not even know about topics/queues/subjects or any broker inner objects you use.
The basic syntax is the same for all brokers:

{! includes/getting_started/subscription/index/1.md !}

!!! tip
    If you want to use Message Broker specific features, please visit the corresponding broker documentation section.
    In the **Tutorial** section, the general features are described.

Also, synchronous functions are supported as well:

{! includes/getting_started/subscription/index/sync.md !}

## Message Body Serialization

Generally, **FastStream** uses your function type annotation to serialize incoming message body with [**Pydantic**](https://docs.pydantic.dev){.external-link target="_blank"}. This is similar to how [**FastAPI**](https://fastapi.tiangolo.com){.external-link target="_blank"} works (if you are familiar with it).

{! includes/getting_started/subscription/index/2.md !}

You can also access some extra features through the function arguments, such as [Depends](../dependencies/index.md){.internal-link} and [Context](../context/existed.md){.internal-link} if required.

However, you can easily disable **Pydantic** validation by creating a broker with the following option `#!python Broker(apply_types=False)`

This way **FastStream** still consumes `#!python json.loads` result, but without pydantic validation and casting.

{! includes/getting_started/subscription/index/3.md !}

!!! warning
    Setting the `apply_types=False` flag not only disables type casting but also `Depends` and `Context`.
    If you want to disable only type casting, use `serializer=None` instead.

## Multiple Subscriptions

You can also subscribe to multiple event streams at the same time with one function. Just wrap it with multiple `#!python @broker.subscriber(...)` decorators (they have no effect on each other).

{! includes/getting_started/subscription/index/4.md !}
