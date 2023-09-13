# Broker Publishing

Easiest way to publish message

Allows use a Broker like a publisher client in any applications.

In the FastStream project this call not represented in the AsyncAPI scheme, so you can use it to send rarely-publishing messages (like startup/shutdown event).

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/broker_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/broker_rabbit.py !}
    ```
