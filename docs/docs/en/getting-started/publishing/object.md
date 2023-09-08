# Publisher Object

Full-featured way to publish messages (has AsyncAPI representation + testable feaures).
Creates reusable Publisher object.

Can be used as a function decorator

Subscriber and publisher decorators order has no matter, but can be used only with a functions decorated by a `subscriber` too.

Also uses the handler function return type annotation to cast function return before sending (be accurate with it)

{!> includes/getting_started/publishing/object/1.md !}

Can be used multiple times with the one function to broadcast function return

```python
@publisher1
@publisher2
@broker.subscriber("in")
async def handle(msg) -> str:
    return "Response"
```