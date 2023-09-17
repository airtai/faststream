# Subscription Basics

**FastStream** provides you Message Broker agnostic way to subscribe on event streams.

You need no even know about topic/queue/subject or any broker inner objects you use.
The basic syntax is same in for all brokers:

=== "Kafka"
    ```python
    from faststream.kafka import KafkaBroker

    broker = KafkaBroker()

    @broker.subscriber("test")  # topic name
    async def handle_msg(msg_body):
        ...
    ```

=== "RabbitMQ"
    ```python
    from faststream.rabbit import RabbitBroker

    broker = RabbitBroker()

    @broker.subscriber("test")  # queue name
    async def handle_msg(msg_body):
        ...
    ```

!!! tip
    If you want to use Message Broker specific features, please visit corresponding broker documentation section.
    In the **Tutorial** section the general features are described.

Also, synchronous functions are supported as well:

=== "Kafka"
    ```python
    from faststream.kafka import KafkaBroker

    broker = KafkaBroker()

    @broker.subscriber("test")  # topic name
    def handle_msg(msg_body):
        ...
    ```

=== "RabbitMQ"
    ```python
    from faststream.rabbit import RabbitBroker

    broker = RabbitBroker()

    @broker.subscriber("test")  # queue name
    def handle_msg(msg_body):
        ...
    ```

## Message body serialization

Generally, **FastStream** uses your function type annotation to serialize incoming message body by [**Pydantic**](https://docs.pydantic.dev){.external-link target="_blank"}. It is pretty close to how [**FastAPI**](https://fastapi.tiangolo.com){.external-link target="_blank"} works (if you are familiar with it).

```python
@broker.subscriber("test")
async def handle_str(msg_body: str):
    ...
```

Also, through the function arguments you can get access to some extra features: [Depends](../dependencies/index.md){.internal-link} and [Context](../context/existed.md){.internal-link} if it is required.

But you can easely disable pydantic validation by creation a broker with the following option `#!python Broker(apply_types=False)` (disables Context and Depends features too)

This way **FastStream** still consumes `#!python json.loads` result, but without pydantic validation and casting.

=== "Kafka"
    ```python
    from faststream.kafka import KafkaBroker

    broker = KafkaBroker(apply_types=False)

    @broker.subscriber("test")
    async def handle_msg(msg_body: str):  # just an annotation, has no real effect
        ...
    ```

=== "RabbitMQ"
    ```python
    from faststream.rabbit import RabbitBroker

    broker = RabbitBroker(apply_types=False)

    @broker.subscriber("test")
    async def handle_msg(msg_body: str):  # just an annotation, has no real effect
        ...
    ```

## Multiple Subscriptions

Also, you are able to subscribe on multiple event streams in the same time with the one function. Just wrap it by multiple `#!python @broker.subscriber(...)` decorators (they have no effect on each other)

```python
@broker.subscriber("first_sub")
@broker.subscriber("second_sub")
async def handler(msg):
    ...
```
