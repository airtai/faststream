# Custom Parser

At this stage, **FastStream** serializes an incoming message of the framework that is used to work with the broker into a general view - **StreamMessage**. At this stage, the message body remains in the form of raw bytes.

**StreamMessage** - is a general **FastStream** message view. It contains total information about message required inside **FastStreams**. It is using to represent even a messages batches, so the only one reason to customize it - **FastStream** message metainformation redefinition.

As an example: you can specify your own header with the `message_id` semantic. So, you can inform **FastStream** about it by parser customization.

## Signature

To create a custom message parser you should write a regular (sync or async) python function with the following signature:

=== "Kafka"
    ``` python
    from aiokafka import ConsumerRecord
    from faststream.kafka import KafkaMessage

    def parser(msg: ConsumerRecord) -> KafkaMessage:
        ...
    ```

=== "RabbitMQ"
    ``` python
    from aio_pika import IncomingMessage
    from faststream.rabbit import RabbitMessage

    def parser(msg: IncomingMessage) -> RabbitMessage:
        ...
    ```

Also, you are able to reuse the original parser function by using next signature

=== "Kafka"
    ``` python
    from types import Callable, Awaitable
    from aiokafka import ConsumerRecord
    from faststream.kafka import KafkaMessage

    async def parser(
        msg: ConsumerRecord,
        original_parser: Callable[[ConsumerRecord], Awaitable[KafkaMessage]],
    ) -> KafkaMessage:
        return await original_parser(msg)
    ```

=== "RabbitMQ"
    ``` python
    from types import Callable, Awaitable
    from aio_pika import IncomingMessage
    from faststream.rabbit import RabbitMessage

    async def parser(
        msg: IncomingMessage,
        original_parser: Callable[[IncomingMessage], Awaitable[RabbitMessage]],
    ) -> RabbitMessage:
        return await original_parser(msg)
    ```

All arguments naming has no matter, parser will be always placed to the second one.

!!! note
    Original parser is always async function, so your custom one should be an async too

After you can set this parser at broker or subsriber level both.

## Example

As an example, let's redefine `message_id` to the custom header


=== "Kafka"
    ``` python linenums="1" hl_lines="8-14 17 28"
    {!> docs_src/getting_started/serialization/parser_kafka.py !}
    ```

=== "RabbitMQ"
    ``` python linenums="1" hl_lines="8-14 17 28"
    {!> docs_src/getting_started/serialization/parser_rabbit.py !}
    ```
