# Serialization examples

## Protobuf

In this section, we will look at an example using *Protobuf*, however, it is also applicable for any other serialization methods.

???- note "Protobuf"
    *Protobuf* is an alternative message serialization method commonly used in *GRPC*. Its main advantage is much smaller [^1] message size (compared to *JSON*), but it requires a message schema (`.proto` files) both on the client side and on the server side.

To begin with, install the dependencies:

```console
pip install grpcio-tools
```

Then we will describe the scheme of our message

```proto title="message.proto"
syntax = "proto3";

message Person {
    string name = 1;
    float age = 2;
}
```

Now we will generate a *Python* class for working with messages in the *Protobuf format*

```console
python -m grpc_tools.protoc --python_out=. --pyi_out=. -I . message.proto
```

At the output, we get 2 files: `message_pb2.py` and `message_pb2.pyi`. Now we are ready to use the generated class to serialize our messages.

``` python linenums="1" hl_lines="1 10-13 16 23"
from message_pb2 import Person

from faststream import FastStream, Logger, NoCast
from faststream.rabbit import RabbitBroker, RabbitMessage

broker = RabbitBroker()
app = FastStream(broker)


async def decode_message(msg: RabbitMessage) -> Person:
    decoded = Person()
    decoded.ParseFromString(msg.body)
    return decoded


@broker.subscriber("test", decoder=decode_message)
async def consume(body: NoCast[Person], logger: Logger):
    logger.info(body)


@app.after_startup
async def publish():
    body = Person(name="john", age=25).SerializeToString()
    await broker.publish(body, "test")
```

Note that we used the `NoCast` annotation, which excludes the message from the `pydantic` representation of our handler.

``` python
async def consume(body: NoCast[Person], logger: Logger):
```

## Msgpack

*Msgpack* is an alternative binary data format too. Its main advantage is smaller [^2] than *JSON* message size (but a little bigger than *Protobuf*) and it doesn't require any message schema (*Protobuf* does). So, you can easily use it in the most cases.

First of all, install the dependencies:

```console
pip install msgpack
```

And, because you need no any schema, you can easely write a *Msgpack* decoder:

``` python linenums="1" hl_lines="1 10-11 14 21"
import msgpack

from faststream import FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitMessage

broker = RabbitBroker()
app = FastStream(broker)


async def decode_message(msg: RabbitMessage):
    return msgpack.loads(msg.body)


@broker.subscriber("test", decoder=decode_message)
async def consume(body, logger: Logger):
    logger.info(body)


@app.after_startup
async def publish():
    body = msgpack.dumps({"name": "john", "age": 25}, use_bin_type=True)
    await broker.publish(body, "test")
```

It is much easier than *Protobuf* schema usage. Thus, if you have no strict msg size limitations, you able to use *Msgpack* serialization almost everywhere.

## Tips

### Data compression

Also, if you are sending a really huge messages, you should try to compress them too. As an example, take a look at [**lz4**](https://github.com/python-lz4/python-lz4){.external-link targer="_blank"} or [**zstd**](https://github.com/sergey-dryabzhinsky/python-zstd){.external-link targer="_blank"} algorythms.

This way you can reduce message size if it has some repeated blocks, but at the small message body cases data compressing able to extend it. So, you need to check compression effort in your application specific case.

### Broker-level serialization

You are still able to set custom `decoder` on the Broker or Router level too. But, if you want to encode publishing messages automatically too, you should take a look at [Middleware](../middlewares/index.md){.internal-link} serialization implimentation.

[^1]:
    For example, a message like `#!json { "name": "john", "age": 25 }` in *JSON* takes **27** bytes, and in *Protobuf* - **11**. With lists and more complex structures, the savings can be even more significant (up to 20x times).

[^2]:
    `#!json {"name": "john", "age": 25 }` with *Msgpack* serialization takes **16** bytes.
