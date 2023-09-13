# Application-level filtering

Allows to specify message processing way by message headers, body type or smth else

Message must be consumed be the ONE consumer (not some of them)

Subscriber without filter - default subscriber. Consumes messages, not consumed by other filters.

=== "Kafka"
    ```python linenums="1" hl_lines="8 14"
    {!> docs_src/getting_started/subscription/filter_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="8 14"
    {!> docs_src/getting_started/subscription/filter_rabbit.py !}
    ```
