# Custom Decoder

At this stage, the body of **StreamMessage** is transformed to the form in which it enters your handler function. This method you will have to redefine more often.

## Signature

In the original, its signature is quite simple (this is a simplified version):

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

Also, you are able to reuse the original decoder function by using next signature

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
    Original decoder is always async function, so your custom one should be an async too

After you can set this decoder at broker or subsriber level both.

## Example

You can find *Protobuf* and *Msgpack* serialization examples in the [next](./examples.md){.internal-link} article.
