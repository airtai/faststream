# Existing fields

**Context** already contains some global objects that you can always access:

* **broker** - current broker
* **context** - the context itself, in which you can write your own fields
* **logger** - logger used for your broker (tags messages with *message_id*)
* **message** - raw message (if you need access to it)

At the same time, thanks to `contextlib.ContextVar`, **message** is local for you current consumer scope.

## Access to context fields

By default the context searches for an object based on the argument name.

=== "Kafka"
    ```python linenums="1" hl_lines="1 12-15"
    {!> docs_src/getting_started/context/existed_context_kafka.py [ln:1-2,10-11,14-23] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="1 12-15"
    {!> docs_src/getting_started/context/existed_context_rabbit.py [ln:1-2,10-11,14-23] !}
    ```

## Annotated aliases

Also, **FastStream** has already created `Annotated` aliases to provide you comfortable access to already existing objects. You can import them right from `faststream` or your broker-specific modules:

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

To apply them, just import and use as a subscriber argument annotation

=== "Kafka"
    ```python linenums="1" hl_lines="3-8 17-20"
    {!> docs_src/getting_started/context/existed_context_kafka.py [ln:1-11,26-35] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="3-8 17-20"
    {!> docs_src/getting_started/context/existed_context_rabbit.py [ln:1-11,26-35] !}
    ```
