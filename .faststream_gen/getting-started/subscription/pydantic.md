# Pydantic Serialization

## pydantic.Field

Besides, **FastStream** uses your handlers' annotations to collect information about apllication schema and generate [**AsyncAPI**](https://www.asyncapi.com){.external-link target="_blank"} schema.

You may reach this information by extra details using `pydantic.Field` (like title, description and examples). Also [Fields](https://docs.pydantic.dev/latest/usage/fields/){.external-link target="_blank"} usage allows you to add some extra validations to your message schema.

Just use `pydantic.Field` as a function default argument

=== "Kafka"
    ```python linenums="1" hl_lines="12-17"
    {!> docs_src/getting_started/subscription/pydantic_fields_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="12-17"
    {!> docs_src/getting_started/subscription/pydantic_fields_rabbit.py !}
    ```

## pydantic.BaseModel

To make your message schema reusable between different subscribers and publishers you can decalre it as a `pydantic.BaseModel` and use as a single message annotation

=== "Kafka"
    ```python linenums="1" hl_lines="1 10 20"
    {!> docs_src/getting_started/subscription/pydantic_model_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="1 10 20"
    {!> docs_src/getting_started/subscription/pydantic_model_rabbit.py !}
    ```
