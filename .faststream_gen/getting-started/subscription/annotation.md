# Annotation Serialization

Use type annotation to serialize incoming message body

Allows use all Pydantic specific fields (like HttpUrl, PositiveInt, e.t.c)

Reuse imported block in the different translations

=== "Kafka"
    ```python linenums="1" hl_lines="8"
    {!> docs_src/getting_started/subscription/annotation_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="8"
    {!> docs_src/getting_started/subscription/annotation_rabbit.py !}
    ```
