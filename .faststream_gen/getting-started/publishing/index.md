# Publishing Basics

Broker agnostic, easy to use (even as a client in the not-FastStream apps)

Several usecases

* broker.publish
* decorator
* publisher object decorator
* publisher object direct

Allows to publish any JSON-serializable messages (python types, pydantic models, e.t.c.) or raw bytes.

<<<<<<< HEAD
Automatically setups all required headers (expecially correlation_id, which using to trace message processing pipeline through all services)
=======
Automatically setups all required headers.
>>>>>>> 059c9aba72e2f42df25fa587b154fc4dbc9c0c30

Just setup a message and a routing key

=== "Kafka"
    ```python
    async with KafkaBroker() as br:
        await br.publish("message", "topic")
    ```

=== "Rabbit"
    ```python
    async with RabbitBroker() as br:
        await br.publish("message", "queue")
    ```