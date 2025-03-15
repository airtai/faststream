---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Publisher Direct Usage

The Publisher Object provides a full-featured way to publish messages. It has an [**AsyncAPI**](../asyncapi/custom.md){.internal-link} representation and includes [testability](./test.md){.internal-link} features.

This method creates a reusable Publisher object that can be used directly to publish a message:

!!! tip "Pros and Cons"

    :material-checkbox-marked:{.checked_mark} **AsyncAPI support** - [**```AsyncAPI```**](../asyncapi/export.md#section{.css-styles}) is a specification for describing asynchronous APIs used in messaging applications. This method does not currently support this standard.

    :material-checkbox-marked:{.checked_mark} **No testing support** - This method has full [**```Testing```**](./test.md#section{.css-styles}) support.

    :material-checkbox-marked:{.checked_mark} **Broker availability from Context** - You can leverage **FastStream's** [**```Context```**](../context/index.md#section{.css-styles}), built-in Dependency Injection (DI) container to work with brokers or other external services.

    :material-checkbox-marked:{.checked_mark} **Optional publication** - You can create optional publication

    :material-checkbox-marked:{.checked_mark} **Can be reused** - This method is reusable.


{! includes/getting_started/publishing/direct/1.md !}

It is something in the middle between [broker publish](./broker.md){.internal-link} and [object decorator](./object.md){.internal-link}. It has an **AsyncAPI** representation and *testability* features (like the **object decorator**), but allows you to send different messages to different outputs (like the **broker publish**).

```python hl_lines="3-4"
@broker.subscriber("in")
async def handle(msg) -> str:
    await publisher1.publish("Response-1")
    await publisher2.publish("Response-2")
```

!!! note
    When using this method, **FastStream** doesn't reuse the incoming `correlation_id` to mark outgoing messages with it. You should set it manually if it is required.
