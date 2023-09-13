# Publisher Object

Full-featured way to publish messages (has AsyncAPI representation + testable feaures).
Creates reusable Publisher object.

Can be used as a function decorator

Subscriber and publisher decorators order has no matter, but can be used only with a functions decorated by a `subscriber` too.

Also uses the handler function return type annotation to cast function return before sending (be accurate with it)

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_rabbit.py !}
    ```

Can be used multiple times with the one function to broadcast function return

```python
@publisher1
@publisher2
@broker.subscriber("in")
async def handle(msg) -> str:
    return "Response"
```

Also, it automatically sends a message with the same with incoming message `correlation_id`. This way you get the same `correlation_id` for the one message pipeline procces inside all services and able to collect a trace.
