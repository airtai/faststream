# Existing Fields

**Context** already contains some global objects that you can always access:

* **broker** - the current broker
* **context** - the context itself, in which you can write your own fields
* **logger** - the logger used for your broker (tags messages with *message_id*)
* **message** - the raw message (if you need access to it)

At the same time, thanks to `contextlib.ContextVar`, **message** is local for you current consumer scope.

## Access to Context Fields

By default, the context searches for an object based on the argument name.

=== "Kafka"
    ```python linenums="1" hl_lines="1 12-15"
    {!> docs_src/getting_started/context/existed_context_kafka.py [ln:1-2,10-11,14-23] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="1 12-15"
    {!> docs_src/getting_started/context/existed_context_rabbit.py [ln:1-2,10-11,14-23] !}
    ```

## Annotated Aliases

Also, **FastStream** has already created `Annotated` aliases to provide you with comfortable access to existing objects. You can import them directly from `faststream` or your broker-specific modules:

* Shared aliases

```python
from faststream import Logger, ContextRepo
```

* *Kafka* aliases

```python
from faststream.kafka.annotations import (
    Logger, ContextRepo, KafkaMessage, KafkaBroker, KafkaProducer
)
```

* *RabbitMQ* aliases

```python
from faststream.rabbit.annotations import (
    Logger, ContextRepo, RabbitMessage, RabbitBroker, RabbitProducer
)
```

To use them, simply import and use them as subscriber argument annotations.

=== "Kafka"
    ```python linenums="1" hl_lines="3-8 17-20"
    {!> docs_src/getting_started/context/existed_context_kafka.py [ln:1-11,26-35] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="3-8 17-20"
    {!> docs_src/getting_started/context/existed_context_rabbit.py [ln:1-11,26-35] !}
    ```
