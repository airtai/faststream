# Existing Fields

**Context** already contains some global objects that you can always access:

* **broker** - the current broker
* **context** - the context itself, in which you can write your own fields
* **logger** - the logger used for your broker (tags messages with *message_id*)
* **message** - the raw message (if you need access to it)

At the same time, thanks to `contextlib.ContextVar`, **message** is local for you current consumer scope.

## Access to Context Fields

By default, the context searches for an object based on the argument name.

{!> includes/getting_started/context/access.md !}

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

* *NATS* aliases

```python
from faststream.rabbit.annotations import (
    Logger, ContextRepo, NatsMessage,
    NatsBroker, NatsProducer, NatsJsProducer,
    Client, JsClient,
)
```

To use them, simply import and use them as subscriber argument annotations.

{!> includes/getting_started/context/existed_annotations.md !}
