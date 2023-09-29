# Object Storage

Object storage - almost literally the same with the [*Key-Value*](./key-value.md) stroge thing, so you can reuse it guide.

## Overview

[*Object Storage*](https://docs.nats.io/nats-concepts/jetstream/obj_store){.external-link target="_blank"} storage just a high-level interface on top of *NatsJS*.

It is a regular *JetStream*, where *Object key* is a subject.

The main difference between *KV* and *Object* storages that in the *Object* one you can store files greater than **1MB** (*KV* limitation). It has no limit on the maximum object size and stores it by chunks (each message is an object chunk), so you can literally *stream* huge objects through the *NATS*.

## FastStream Details

**FastStream** has no native interfaces to this *NatsJS* functionality (yet), but allows you to get access into the inner `JetStream` object to create in manually.

First of all, you need to create *Object* storage object and pass in to the context:

```python linenums="1" hl_lines="14-15"
from faststream import Context, FastStream
from faststream.nats import NatsBroker
from faststream.nats.annotations import ContextRepo
broker = NatsBroker()
app = FastStream(broker)
@app.on_startup
async def setup_broker(context: ContextRepo):
    await broker.connect()

    os = await broker.stream.create_object_store("bucket")
    context.set_global("OS", os)
```

!!! tip
    We made in `#!python @app.on_startup` hook because `#!python @app.after_startup` will be triggered **AFTER** your handlers start to consume message. So, if you need to have access to any custom context objects, you should set them in `#!python @app.on_startup` hook.

    Also, we call `#!python await broker.connect()` method manually to have extablished connection to be able to create a storage.

---

Next Step we are ready to use this object right in the our handlers.

Lets create an Annotated object to shorter Context object access

```python linenums="1" hl_lines="5"
from nats.js.object_store import ObjectStore as OS
from typing_extensions import Annotated
ObjectStorage = Annotated[OS, Context("OS")]
```

And just use it in a handler

```python linenums="1" hl_lines="8 10-11"
from io import BytesIO
from faststream import Logger
@broker.subscriber("subject")
async def handler(msg: str, os: ObjectStorage, logger: Logger):
    logger.info(msg)
    obj = await os.get("file")
    assert obj.data == b"File mock"
```

Finally, lets test our code behavior by putting smth to *KV storage* and sending a message:

```python linenums="1" hl_lines="3-4"
@app.after_startup
async def test_send(os: ObjectStorage):
    await os.put("file", BytesIO(b"File mock"))
    await broker.publish("Hi!", "subject")
```

!!! tip
    [`BytesIO`](https://docs.python.org/3/library/io.html#binary-i-o){.external-link target="_blank"} - is an *Readable* object to emulate opened to read file.

??? example "Full listing"
    ```python linenums="1"
from io import BytesIO

from nats.js.object_store import ObjectStore as OS
from typing_extensions import Annotated

from faststream import Logger
from faststream import Context, FastStream
from faststream.nats import NatsBroker
from faststream.nats.annotations import ContextRepo

ObjectStorage = Annotated[OS, Context("OS")]

broker = NatsBroker()
app = FastStream(broker)


@broker.subscriber("subject")
async def handler(msg: str, os: ObjectStorage, logger: Logger):
    logger.info(msg)
    obj = await os.get("file")
    assert obj.data == b"File mock"


@app.on_startup
async def setup_broker(context: ContextRepo):
    await broker.connect()

    os = await broker.stream.create_object_store("bucket")
    context.set_global("OS", os)


@app.after_startup
async def test_send(os: ObjectStorage):
    await os.put("file", BytesIO(b"File mock"))
    await broker.publish("Hi!", "subject")
    ```
