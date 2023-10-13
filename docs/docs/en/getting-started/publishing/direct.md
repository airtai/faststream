# Publisher Direct Usage

The Publisher Object provides a full-featured way to publish messages. It has an [**AsyncAPI**](../asyncapi/custom.md){.internal-link} representation and includes [testability](./test.md){.internal-link} features.

This method creates a reusable Publisher object that can be used directly to publish a message:

{!> includes/getting_started/publishing/direct/1.md !}

It is something in the middle between [broker publish](./broker.md){.internal-link} and [object decorator](./object.md){.internal-link}. It has an **AsyncAPI** representation and *testability* features (like the **object decorator**), but allows you to send different messages to different outputs (like the **broker publish**).

```python
@broker.subscriber("in")
async def handle(msg) -> str:
    await publisher1.publish("Response-1")
    await publisher2.publish("Response-2")
```

!!! note
    When using this method, **FastStream** doesn't reuse the incoming `correlation_id` to mark outgoing messages with it. You should set it manually if it is required.
