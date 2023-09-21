# Application Context

**FastStreams** has its own Dependency Injection container - **Context**, used to store application runtime objects and variables.

With this container, you can access both application scope and message processing scope objects. This functionality is similar to [`Depends`](../dependencies/index.md){.internal-link} usage.

=== "Kafka"
    ```python linenums="1" hl_lines="1 11"
    {!> docs_src/getting_started/context/base_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="1 11"
    {!> docs_src/getting_started/context/base_rabbit.py !}
    ```

But, with the [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated){.external-docs target="_blank"} Python feature usage, it is much closer to `#!python @pytest.fixture`.

=== "Kafka"
    ```python linenums="1" hl_lines="1 6 15"
    {!> docs_src/getting_started/context/annotated_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="1 6 15"
    {!> docs_src/getting_started/context/annotated_rabbit.py !}
    ```

## Usages

By default, the context is available in the same place as `Depends`:

* at lifespan hooks
* message subscribers
* nested dependencies

!!! tip
    Fields obtained from the `Context` are editable, so editing them in a function means editing them everywhere.

## Compatibility with Regular Functions

To use context in other functions, use the `#!python @apply_types` decorator. In this case, the context of the called function will correspond to the context of the event handler from which it was called.

```python linenums="1" hl_lines="6 8 11"
from faststream import Context, apply_types


@broker.subscriber("test")
async def handler(body: dict):
    nested_func()


@apply_types
def nested_func(body: dict, logger=Context()):
    logger.info(body)
```

In the example above, we did not pass the `logger` function at calling it; it was placed outside of context.
