# Serialization examples

## Protobuf

In this section, we will explore an example using *Protobuf*. However, this approach is also applicable to other serialization methods.

???- note "Protobuf"
    *Protobuf* is an alternative message serialization method commonly used in *GRPC*.  Its main advantage is that it results in much smaller message sizes[^1] compared to *JSON*, but it requires a message schema (`.proto` files) on both the client and server sides.

To begin, install the necessary dependencies:

```console
pip install grpcio-tools
```

Next, let's define the schema for our message:

```proto title="message.proto"
syntax = "proto3";

message Person {
    string name = 1;
    float age = 2;
}
```

Now, generate a *Python* class to work with messages in *Protobuf format*:

```console
python -m grpc_tools.protoc --python_out=. --pyi_out=. -I . message.proto
```

This generates two files: `message_pb2.py` and `message_pb2.pyi`. We can use the generated class to serialize our messages:

``` python linenums="1" hl_lines="1 10-13 16 23"
{!> docs_src/getting_started/serialization/protobuf.py !}
```

Note that we used the `NoCast` annotation to exclude the message from the `pydantic` representation of our handler.

``` python
{!> docs_src/getting_started/serialization/protobuf.py [ln:17] !}
```

## Msgpack

*Msgpack* is another alternative binary data format. Its main advantage is that it results in smaller message sizes[^2] compared to *JSON*, although slightly larger than *Protobuf*. The key advantage is that it doesn't require a message schema, making it easy to use in most cases.

To get started, install the necessary dependencies:

```console
pip install msgpack
```

Since there is no need for a schema, you can easily write a *Msgpack* decoder:

``` python linenums="1" hl_lines="1 10-11 14 21"
{!> docs_src/getting_started/serialization/msgpack_ex.py !}
```

Using *Msgpack* is much simpler than using *Protobuf* schemas. Therefore, if you don't have strict message size limitations, you can use *Msgpack* serialization in most cases.

## Tips

### Data Compression

If you are dealing with very large messages, consider compressing them as well. You can explore libraries such as [**lz4**](https://github.com/python-lz4/python-lz4){.external-link targer="_blank"} or [**zstd**](https://github.com/sergey-dryabzhinsky/python-zstd){.external-link targer="_blank"} for compression algorithms.

Compression can significantly reduce message size, especially if there are repeated blocks. However, in the case of small message bodies, data compression may increase the message size. Therefore, you should assess the compression impact based on your specific application requirements.

### Broker-Level Serialization

You can still set a custom `decoder` at the Broker or Router level. However, if you want to automatically encode publishing messages as well, you should explore [Middleware](../middlewares/index.md){.internal-link} for serialization implimentation.

[^1]:
    For example, a message like `#!json { "name": "John", "age": 25 }` in *JSON* takes **27** bytes, while in *Protobuf*, it takes only **11** bytes. With lists and more complex structures, the savings can be even more significant (up to 20x times).

[^2]:
    A message with *Msgpack* serialization, such as `#!json { "name": "John", "age": 25 }`, takes **16** bytes.
