# Publisher Direct Usage

The Publisher Direct Usage is a full-featured way to publish messages. It has AsyncAPI representation and includes testable features. This method creates a reusable Publisher object that can be used directly to publish a message:

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/direct_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/direct_rabbit.py !}
    ```

It is suitable for publishing different messages to different outputs within the same processing function:

```python
@broker.subscriber("in")
async def handle(msg) -> str:
    await publisher1.publish("Response-1")
    await publisher2.publish("Response-2")
```
