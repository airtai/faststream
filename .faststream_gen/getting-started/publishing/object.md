# Publisher Object

The Publisher Object provides a full-featured way to publish messages. It has **AsyncAPI** representation and includes testable features. This method creates a reusable Publisher object.

It can be used as a function decorator. The order of Subscriber and Publisher decorators doesn't matter, but they can only be used with functions decorated by a `subscriber` decorator.

It also uses the handler function's return type annotation to cast the function's return value before sending, so be accurate with it:

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_rabbit.py !}
    ```

You can use it multiple times with one function to broadcast the function's return:

```python
@publisher1
@publisher2
@broker.subscriber("in")
async def handle(msg) -> str:
    return "Response"
```

Additionally, it automatically sends a message with the same `correlation_id` as the incoming message. This way, you get the same correlation_id for the entire message pipeline process across all services, allowing you to collect a trace.
