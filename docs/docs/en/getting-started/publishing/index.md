# Publishing Basics

**FastStream** is broker-agnostic and easy to use, even as a client in non-FastStream applications.

It offers several use cases for publishing messages:

* Using `broker.publish``
* Using a decorator
* Using a publisher object decorator
* Using a publisher object directly

**FastStream** allows you to publish any JSON-serializable messages (Python types, Pydantic models, e.t.c.) or raw bytes.

It automatically sets up all required headers, especially the correlation_id, which is used to trace message processing pipelines across all services.

To publish a message, simply set up the message content and a routing key:

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
