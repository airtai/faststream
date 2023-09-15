# Context Extra options

Also, `Context` provides you some extra abilities to work with a containing object.

## Default values

As an example, if you try to access a field that does not exist in the global context, you will get the `pydantic.ValidationError` exception.

However, you can set the default value if you feel the need.

=== "Kafka"
    ```python linenums="1" hl_lines="3 5"
    {!> docs_src/getting_started/context/default_arguments_kafka.py [ln:7-11] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="3 5"
    {!> docs_src/getting_started/context/default_arguments_rabbit.py [ln:7-11] !}
    ```

## Cast context types

By default, context fields are **NOT CAST** to the type specified in their annotation.

=== "Kafka"
    ```python linenums="1" hl_lines="6 10 12"
    {!> docs_src/getting_started/context/cast_kafka.py [ln:1-12] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="6 10 12"
    {!> docs_src/getting_started/context/cast_rabbit.py [ln:1-12] !}
    ```

If you need this functionality, you can set the appropriate flag.

=== "Kafka"
    ```python linenums="1" hl_lines="3 5"
    {!> docs_src/getting_started/context/cast_kafka.py [ln:14-18] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="3 5"
    {!> docs_src/getting_started/context/cast_rabbit.py [ln:14-18] !}
    ```
