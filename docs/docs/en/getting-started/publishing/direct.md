# Publisher Direct Usage

Full-featured way to publish messages (has AsyncAPI representation + testable feaures).
Creates reusable Publisher object.

Can be used directly to publush a message

{!> includes/getting_started/publishing/direct/1.md !}

Suitable to publish different messages to different outputes at the same processing function

```python
@broker.subscriber("in")
async def handle(msg) -> str:
    await publisher1.publish("Response-1")
    await publisher2.publish("Response-2")
```
