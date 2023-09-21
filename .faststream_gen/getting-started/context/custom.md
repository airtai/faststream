# Context Fields Declaration

You can also store your own objects in the `Context`.

## Global

To declare an application-level context field, you need to call the `context.set_global` method with with a key to indicate where the object will be placed in the context.

=== "Kafka"
    ```python linenums="1" hl_lines="9-10"
    {!> docs_src/getting_started/context/custom_global_context_kafka.py [ln:1-5,16-18] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="9-10"
    {!> docs_src/getting_started/context/custom_global_context_rabbit.py [ln:1-5,16-18] !}
    ```

Afterward, you can access your `secret` field in the usual way:

=== "Kafka"
    ```python linenums="1" hl_lines="4"
    {!> docs_src/getting_started/context/custom_global_context_kafka.py [ln:8-13] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="4"
    {!> docs_src/getting_started/context/custom_global_context_rabbit.py [ln:8-13] !}
    ```

In this case, the field becomes a global context field: it does not depend on the current message handler (unlike `message`)

To remove a field from the context use the `reset_global` method:

```python
context.reset_global("my_key")
```

## Local

To set a local context (available only within the message processing scope), use the context manager `scope`

=== "Kafka"
    ```python linenums="1" hl_lines="15 19 21-22"
    {!> docs_src/getting_started/context/custom_local_context_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="15 19 21-22"
    {!> docs_src/getting_started/context/custom_local_context_rabbit.py !}
    ```

You can also set the context yourself, and it will remain within the current call stack until you clear it.

=== "Kafka"
    ```python linenums="1" hl_lines="1 14 24"
    {!> docs_src/getting_started/context/manual_local_context_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="1 14 24"
    {!> docs_src/getting_started/context/manual_local_context_rabbit.py !}
    ```
