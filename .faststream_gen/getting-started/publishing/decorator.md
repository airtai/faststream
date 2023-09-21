# Publisher Decorator

The second easiest way to publish messages is by using the Publisher Decorator. This method has an AsyncAPI representation and is suitable for quickly creating applications. However, it doesn't provide all testing features.

It creates a structured DataPipeline unit with an input and output. The order of Subscriber and Publisher decorators doesn't matter, but they can only be used with functions decorated by a `subscriber` as well.

It uses the handler function's return type annotation to cast the function's return value before sending, so be accurate with it:

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/decorator_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/decorator_rabbit.py !}
    ```

It can be used multiple times with one function to broadcast the function's return:

```python
@broker.subscriber("in")
@broker.publisher("first-out")
@broker.publisher("second-out")
async def handle(msg) -> str:
    return "Response"
```

Additionally, it automatically sends a message with the same `correlation_id` as the incoming message. This way, you get the same `correlation_id` for the entire message pipeline process across all services, allowing you to collect a trace.
