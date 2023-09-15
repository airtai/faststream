# Publishing Basics

Broker agnostic, easy to use (even as a client in the not-FastStream apps)

Several usecases

* broker.publish
* decorator
* publisher object decorator
* publisher object direct

Allows to publish any JSON-serializable messages (python types, pydantic models, e.t.c.) or raw bytes.

Automatically setups all required headers (especially correlation_id, which using to trace message processing pipeline through all services)

Just setup a message and a routing key

=== "Kafka"
    ```python
    async with KafkaBroker() as br:
        await br.publish("message", "topic")
    ```

=== "RabbitMQ"
    ```python
    async with RabbitBroker() as br:
        await br.publish("message", "queue")
    ```
