# Key-Value Storage

## Overview

[*Key-Value*](https://docs.nats.io/nats-concepts/jetstream/key-value-store){.external-link target="_blank"} storage is just a high-level interface on top of *NatsJS*.

It is a regular *JetStream*, where the *KV key* is a subject.

`Put`/`Update` an object to *KV* by *key* - it's like publishing a new message to the corresponding subject in the stream.

Thus, the `Get` command returns not only the current *key* value but the latest one with an offset of it. Additionally, you can ask for a specific value based on its offset in the *KV* stream.

This interface provides you with rich abilities to use it like a regular *KV* storage (ignoring offset) + subscribe to *KV key* changes + ask for an old *KV value* revision. So you can use this feature in your application in a really different way. You can find some examples on the *NATS* developers' official [YouTube channel](https://youtube.com/@NATS_io?si=DWHvNFjsLruxg5OZ){.external-link target="_blank"}

## FastStream Details

**FastStream** has no native interfaces to this *NatsJS* functionality (yet), but it allows you to get access into the inner `JetStream` object to create it manually.

First of all, you need to create a *Key-Value* storage object and pass it into the context:

```python linenums="1" hl_lines="14-15"
from faststream import Context, FastStream, Logger
from faststream.nats import NatsBroker
from faststream.nats.annotations import ContextRepo
broker = NatsBroker()
app = FastStream(broker)
@app.on_startup
async def setup_broker(context: ContextRepo):
    await broker.connect()

    kv = await broker.stream.create_key_value(bucket="bucket")
    context.set_global("kv", kv)
```

!!! tip
    We placed this code in `#!python @app.on_startup` hook because `#!python @app.after_startup` will be triggered **AFTER** your handlers start consuming messages. So, if you need to have access to any custom context objects, you should set them up in the `#!python @app.on_startup` hook.

    Also, we call `#!python await broker.connect()` method manually to establish the connection to be able to create a storage.

---

Next, we are ready to use this object right in our handlers.

Let's create an annotated object to shorten context object access:

```python linenums="1" hl_lines="5"
from nats.js.kv import KeyValue as KV
from typing_extensions import Annotated
KeyValue = Annotated[KV, Context("kv")]
```

And just use it in a handler:

```python linenums="1" hl_lines="4 7-8"
from faststream import Logger
@broker.subscriber("subject")
async def handler(msg: str, kv: KeyValue, logger: Logger):
    logger.info(msg)
    kv_data = await kv.get("key")
    assert kv_data.value == b"Hello!"
```

Finally, let's test our code behavior by putting something into the KV storage and sending a message:

```python linenums="1" hl_lines="3-4"
@app.after_startup
async def test_send(kv: KeyValue):
    await kv.put("key", b"Hello!")
    await broker.publish("Hi!", "subject")
```

??? example "Full listing"
    ```python linenums="1"
from nats.js.kv import KeyValue as KV
from typing_extensions import Annotated

from faststream import Logger
from faststream import Context, FastStream, Logger
from faststream.nats import NatsBroker
from faststream.nats.annotations import ContextRepo

KeyValue = Annotated[KV, Context("kv")]

broker = NatsBroker()
app = FastStream(broker)


@broker.subscriber("subject")
async def handler(msg: str, kv: KeyValue, logger: Logger):
    logger.info(msg)
    kv_data = await kv.get("key")
    assert kv_data.value == b"Hello!"


@app.on_startup
async def setup_broker(context: ContextRepo):
    await broker.connect()

    kv = await broker.stream.create_key_value(bucket="bucket")
    context.set_global("kv", kv)


@app.after_startup
async def test_send(kv: KeyValue):
    await kv.put("key", b"Hello!")
    await broker.publish("Hi!", "subject")
    ```
