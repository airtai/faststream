# Publisher Direct Usage

Full-featured way to publish messages (has AsyncAPI representation + testable feaures).
Creates reusable Publisher object.

Can be used directly to publush a message

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/direct_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/direct_rabbit.py !}
    ```

Suitable to publish different messages to different outputes at the same processing function

```python
@broker.subscriber("in")
async def handle(msg) -> str:
    await publisher1.publish("Response-1")
    await publisher2.publish("Response-2")
```
