# Publisher Decorator

The second easy way to publish messages. Has an AsyncAPI representation.
Suitable for fast application creation, but doesn't provide all testing features.

Creates a structured DataPipeline unit with an input and output

Subscriber and publisher decorators order has no matter, but can be used only with a functions decorated by a `subscriber` too.

Uses the handler function return type annotation to cast function return before sending (be accurate with it)

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/decorator_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/decorator_rabbit.py !}
    ```

Can be used multiple times with the one function to broadcast function return

```python
@broker.subscriber("in")
@broker.publisher("first-out")
@broker.publisher("second-out")
async def handle(msg) -> str:
    return "Response"
```

Also, it automatically sends a message with the same with incoming message `correlation_id`. This way you get the same `correlation_id` for the one message pipeline procces inside all services and able to collect a trace.
