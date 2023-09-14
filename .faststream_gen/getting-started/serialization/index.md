# Custom Serialization

By default, **FastStream** uses the *JSON* format to send and receive messages. However, if you need to handle messages in other formats or with extra serialization steps such as *gzip*, *lz4*, *Avro*, *Protobuf* or *Msgpack*, you can easily modify the serialization logic.

## Serialization Steps

Before the message gets into your subscriber, **FastStream** applies 2 functions to it sequentially: `parse_message` and `decode_message`. You can modify one or both stages depending on your needs.

### Message Parsing

At this stage, **FastStream** serializes an incoming message of the framework that is used to work with the broker into a general view - **StreamMessage**. At this stage, the message body remains in the form of raw bytes.

!!! warning ""
    This stage is strongly related to the features of the broker used and in most cases, its redefinition is not necessary.

The parser declared at the `broker` level will be applied to all subscribers. The parser declared at the `subscriber` level is applied only to this subscriber (it ignores the `broker' parser if it was specified earlier).

### Message Decoding

At this stage, the body of **StreamMessage** is transformed to the form in which it enters your subscriber function. This method you will have to redefine more often.
