# Publisher Testing

If you are working with a Publisher object (either decorator or direct), you can check outgoing messages as well. There are several testing features available:

* In-memory TestClient
* Publishing (including error handling)
* Checking the incoming message body
* Note about mock clearing after the context exits

## Base application

=== "Decorator"
=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_kafka.py[ln:7-12] !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_rabbit.py[ln:7-12] !}
    ```

=== "Direct"
=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/direct_kafka.py[ln:7-11] !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/direct_rabbit.py[ln:7-11] !}
    ```

## Testing

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_kafka_testing.py [ln:1-3,7-12] !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_rabbit_testing.py [ln:1-3,7-12] !}
    ```

* Testing with a real broker
* Waiting for the consumer to be called
