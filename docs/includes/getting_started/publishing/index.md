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


=== "NATS"
    ```python
    async with NatsBroker() as br:
        await br.publish("message", "subject")
    ```
