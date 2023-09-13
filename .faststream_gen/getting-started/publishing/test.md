# Publisher Testing

If you are working with Publisher object (decorator/direct), you able to check outcoming message too

* in-memory TestClient
* publishing (show error raising)
* check incoming message body
* note about mock clearing after context exit

Base application

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

Testing

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_kafka_testing.py [ln:1-3,7-12] !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/publishing/object_rabbit_testing.py [ln:1-3,7-12] !}
    ```

* test with real broker
* wait consumer called
