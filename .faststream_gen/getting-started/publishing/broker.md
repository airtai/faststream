# Broker Publishing

The easiest way to publish a message is to use a Broker, which allows you to use it as a publisher client in any applications.

In the **FastStream** project, this call is not represented in the **AsyncAPI** scheme. You can use it to send rarely-publishing messages, such as startup or shutdown events.

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/broker_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/broker_rabbit.py !}
    ```
