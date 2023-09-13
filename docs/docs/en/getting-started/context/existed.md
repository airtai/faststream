# Existing fields

**Context** already contains some global objects that you can always access:

* **broker** - current broker
* **context** - the context itself, in which you can write your own fields
* **logger** - logger used for your broker (tags messages with *message_id*)
* **message** - raw message (if you need access to it)

At the same time, thanks to `contextlib.ContextVar`, **message** is local for you current consumer scope.

## Access to context fields

By default the context searches for an object based on the argument name.

{!> includes/getting_started/context/access.md !}

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

{!> includes/getting_started/context/existed_annotations.md !}
