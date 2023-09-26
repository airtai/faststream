# Context Extra Options

Additionally, `Context` provides you with some extra capabilities for working with containing objects.

## Default Values

For instance, if you attempt to access a field that doesn't exist in the global context, you will receive a `pydantic.ValidationError` exception.

However, you can set default values if needed.

=== "Kafka"
    ```python linenums="1" hl_lines="3 5"
    {!> docs_src/getting_started/context/default_arguments_kafka.py [ln:7-11] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="3 5"
    {!> docs_src/getting_started/context/default_arguments_rabbit.py [ln:7-11] !}
    ```

## Cast Context Types

By default, context fields are **NOT CAST** to the type specified in their annotation.

=== "Kafka"
    ```python linenums="1" hl_lines="6 10 12"
    {!> docs_src/getting_started/context/cast_kafka.py [ln:1-12] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="6 10 12"
    {!> docs_src/getting_started/context/cast_rabbit.py [ln:1-12] !}
    ```

If you require this functionality, you can enable the appropriate flag.

=== "Kafka"
    ```python linenums="1" hl_lines="3 5"
    {!> docs_src/getting_started/context/cast_kafka.py [ln:14-18] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="3 5"
    {!> docs_src/getting_started/context/cast_rabbit.py [ln:14-18] !}
    ```
