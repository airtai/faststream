# Custom Decoder

At this stage, the body of a **StreamMessage** is transformed into the format that it will take when it enters your handler function. This stage is the one you will need to redefine more often.

## Signature

The original decoder function has a relatively simple signature (this is a simplified version):

=== "Kafka"
    ``` python
    from faststream.types import DecodedMessage
    from faststream.kafka import KafkaMessage

    def decoder(msg: KafkaMessage) -> DecodedMessage:
        ...
    ```

=== "RabbitMQ"
    ``` python
    from faststream.types import DecodedMessage
    from faststream.rabbit import RabbitMessage

    def decoder(msg: RabbitMessage) -> DecodedMessage:
        ...
    ```

Alternatively, you can reuse the original decoder function with the following signature:

=== "Kafka"
    ``` python
    from types import Callable, Awaitable
    from faststream.types import DecodedMessage
    from faststream.kafka import KafkaMessage

    async def decoder(
        msg: KafkaMessage,
        original_decoder: Callable[[KafkaMessage], Awaitable[DecodedMessage]],
    ) -> DecodedMessage:
        return await original_decoder(msg)
    ```

=== "RabbitMQ"
    ``` python
    from types import Callable, Awaitable
    from faststream.types import DecodedMessage
    from faststream.rabbit import RabbitMessage

    async def decoder(
        msg: RabbitMessage,
        original_decoder: Callable[[RabbitMessage], Awaitable[DecodedMessage]],
    ) -> DecodedMessage:
        return await original_decoder(msg)
    ```

!!! note
    The original decoder is always an asynchronous function, so your custom decoder should also be asynchronous.

Afterward, you can set this custom decoder at the broker or subscriber level.

## Example

You can find examples of *Protobuf* and *Msgpack* serialization in the [next article](./examples.md){.internal-link}.
