=== "Kafka"
    ```python
    from faststream.kafka import KafkaBroker

    broker = KafkaBroker()

    @broker.subscriber("test")  # topic name
    def handle_msg(msg_body):
        ...
    ```

=== "RabbitMQ"
    ```python
    from faststream.rabbit import RabbitBroker

    broker = RabbitBroker()

    @broker.subscriber("test")  # queue name
    def handle_msg(msg_body):
        ...
    ```

=== "NATS"
    ```python
    from faststream.nats import NatsBroker

    broker = NatsBroker()

    @broker.subscriber("test")  # subject name
    def handle_msg(msg_body):
        ...
    ```

=== "Redis"
    ```python
    from faststream.redis import RedisBroker

    broker = RedisBroker()

    @broker.subscriber("test")  # channel name
    def handle_msg(msg_body):
        ...
    ```
