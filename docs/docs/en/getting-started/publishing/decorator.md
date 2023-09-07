# Publisher Decorator

The second easy way to publish messages. Has an AsyncAPI representation.
Suitable for fast application creation, but doesn't provide all testing features.

Creates a structured DataPipeline unit with an input and output

Subscriber and publisher decorators order has no matter, but can be used only with a functions decorated by a `subscriber` too.

Uses the handler function return type annotation to cast function return before sending (be accurate with it)

{!> includes/getting_started/publishing/decorator/1.md !}

Can be used multiple times with the one function to broadcast function return

```python
@broker.subscriber("in")
@broker.publisher("first-out")
@broker.publisher("second-out")
async def handle(msg) -> str:
    return "Response"
```