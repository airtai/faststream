# Publisher Direct Usage

The Publisher Direct Usage is a full-featured way to publish messages. It has AsyncAPI representation and includes testable features. This method creates a reusable Publisher object that can be used directly to publish a message:

{!> includes/getting_started/publishing/direct/1.md !}

It is suitable for publishing different messages to different outputs within the same processing function:

```python
@broker.subscriber("in")
async def handle(msg) -> str:
    await publisher1.publish("Response-1")
    await publisher2.publish("Response-2")
```
