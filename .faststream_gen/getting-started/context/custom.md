# Context fields Declaration

Also, you are able to store your own objects in the `Context` for sure.

## Global

To declare an Application-level context fields, you need to call the `context.set_global` method with an indication of the key by which the object will be placed in the context.

=== "Kafka"
    ```python linenums="1" hl_lines="9-10"
    {!> docs_src/getting_started/context/custom_global_context_kafka.py [ln:1-5,16-18] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="9-10"
    {!> docs_src/getting_started/context/custom_global_context_rabbit.py [ln:1-5,16-18] !}
    ```

After you can get access to your `secret` fields in a regular way:

=== "Kafka"
    ```python linenums="1" hl_lines="4"
    {!> docs_src/getting_started/context/custom_global_context_kafka.py [ln:8-13] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="4"
    {!> docs_src/getting_started/context/custom_global_context_rabbit.py [ln:8-13] !}
    ```

In this case, the field becomes a global context field: it does not depend on the current message handler (unlike `message`)

To remove a field from the context use the `reset_global` method

```python
context.reset_global("my_key")
```

## Local

To set the local context (it will be available at the message processing scope), use the context manager `scope`

=== "Kafka"
    ```python linenums="1" hl_lines="15 19 21-22"
    {!> docs_src/getting_started/context/custom_local_context_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="15 19 21-22"
    {!> docs_src/getting_started/context/custom_local_context_rabbit.py !}
    ```

Also, you can set the context yourself: then it will act within the current call stack until you clear it.

=== "Kafka"
    ```python linenums="1" hl_lines="1 14 24"
    {!> docs_src/getting_started/context/manual_local_context_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="1 14 24"
    {!> docs_src/getting_started/context/manual_local_context_rabbit.py !}
    ```
