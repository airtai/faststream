# Subscription Basics

**FastStream** provides you Message Broker agnostic way to subscribe on event streams.

You need no even know about topic/queue/subject or any broker inner objects you use.
The basic syntax is same in for all brokers:

{!> includes/getting_started/subscription/index/1.md !}

!!! tip
    If you want to use Message Broker specific features, please visit corresponding broker documentation section.
    In the **Tutorial** section the general features are described.

Also, synchronous functions are supported as well:

{!> includes/getting_started/subscription/index/sync.md !}

## Message body serialization

Generally, **FastStream** uses your function type annotation to serialize incoming message body by [**Pydantic**](https://docs.pydantic.dev){.external-link target="_blank"}. It is pretty close to how [**FastAPI**](https://fastapi.tiangolo.com){.external-link target="_blank"} works (if you are familiar with it).

{!> includes/getting_started/subscription/index/2.md !}

Also, through the function arguments you can get access to some extra features: [Depends](../dependencies/index.md){.internal-link} and [Context](../context/existed.md){.internal-link} if it is required.

But you can easely disable pydantic validation by creation a broker with the following option `#!python Broker(apply_types=False)` (disables Context and Depends features too)

This way **FastStream** still consumes `#!python json.loads` result, but without pydantic validation and casting.

{!> includes/getting_started/subscription/index/3.md !}

## Multiple Subscriptions

Also, you are able to subscribe on multiple event streams in the same time with the one function. Just wrap it by multiple `#!python @broker.subscriber(...)` decorators (they have no effect on each other)

{!> includes/getting_started/subscription/index/4.md !}
