# Publishing

The **FastStream** KafkaBroker supports all regular [publishing use cases](../getting-started/publishing/index.md){.internal-link}, and you can use them without any changes.

However, if you wish to further customize the publishing logic, you should take a closer look at specific KafkaBroker parameters.

## Basic Kafka Publishing

The `KafkaBroker` uses the unified `publish` method (from a `producer` object) to send messages.

In this case, you can use Python primitives and `pydantic.BaseModel` to define the content of the message you want to publish to the Kafka broker.

You can specify the topic to send by its name.

```python
import asyncio
from faststream.kafka import KafkaBroker

async def pub():
    async with KafkaBroker() as broker:
        await broker.publish(
            "hello_topic",
            "hello!"
        )

asyncio.run(pub())
```

This is the most basic way of using the KafkaBroker to publish a message.
You can see that the broker is used as an async context maanger, which takes care of the startup and shutdown procedures for you.

## Creating a publisher object

The simplest way to use a KafkaBroker for publishing has a significant limitation: your publishers won't be documented in the AsyncAPI documentation. This might be acceptable for sending occasional one-off messages. However, if you're building a comprehensive service, it's recommended to create publisher objects. These objects can then be parsed and documented in your service's AsyncAPI documentation. Let's go ahead and create those publisher objects!

```python
import asyncio
from faststream.kafka import KafkaBroker

broker = KafkaBroker()
publisher = broker.publisher("hello_topic")

async def pub():
    async with KafkaBroker() as broker:
        publisher.publish("Hello!")

asyncio.run(pub())
```

Now, when you wrap your broker into a FastStream object, the publisher will be exported to the AsyncAPI documentation.

## Decorating your publishing functions

To publish messages effectively in the Kafka context, consider utilizing the Publisher Decorator. This approach offers an AsyncAPI representation and is ideal for rapidly developing applications.

The Publisher Decorator creates a structured DataPipeline unit with both input and output components. The sequence in which you apply Subscriber and Publisher decorators does not affect their functionality. However, note that these decorators can only be applied to functions decorated by a Subscriber as well.

This method relies on the return type annotation of the handler function to properly interpret the function's return value before sending it. Hence, it's important to ensure accuracy in defining the return type.

Let's start by examining the entire application that utilizes the Publisher Decorator and then proceed to walk through it step by step.

```python linenums="1"
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream
from faststream.kafka import KafkaBroker


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


to_output_data = broker.publisher("output_data")


@to_output_data
@broker.subscriber("input_data")
async def on_input_data(msg: Data) -> Data:
    return Data(data=msg.data + 1.0)
```
