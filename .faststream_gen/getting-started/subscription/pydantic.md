# Pydantic Serialization

For the most specific cases, where you need to setup extra validations, add something documentation information or smth else

Able to use `pydantic.Field` in a subscriber type annotation

=== "Kafka"
    ```python linenums="1" hl_lines="11-16"
    {!> docs_src/getting_started/subscription/pydantic_fields_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="11-16"
    {!> docs_src/getting_started/subscription/pydantic_fields_rabbit.py !}
    ```

Or make this schema reusable with the `pydantic.BaseModel`

=== "Kafka"
    ```python linenums="1" hl_lines="10-11 14"
    {!> docs_src/getting_started/subscription/pydantic_model_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="10-11 14"
    {!> docs_src/getting_started/subscription/pydantic_model_rabbit.py !}
    ```
