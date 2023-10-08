# Publishing

The **FastStream** KafkaBroker supports all regular [publishing use cases](../../getting-started/publishing/index.md){.internal-link}, and you can use them without any changes.

However, if you wish to further customize the publishing logic, you should take a closer look at specific KafkaBroker parameters.

## Basic Kafka Publishing

The `KafkaBroker` uses the unified `publish` method (from a `producer` object) to send messages.

In this case, you can use Python primitives and `pydantic.BaseModel` to define the content of the message you want to publish to the Kafka broker.

You can specify the topic to send by its name.

1. Create your KafkaBroker instance

```python linenums="1"
broker = KafkaBroker("localhost:9092")
```

2. Publish a message using the `publish` method

```python linenums="1"
        msg = Data(data=0.5)

        await broker.publish(
            model_to_json(msg),
            "input_data",
            headers={"content-type": "application/json"},
        )
```

This is the most basic way of using the KafkaBroker to publish a message.

## Creating a publisher object

The simplest way to use a KafkaBroker for publishing has a significant limitation: your publishers won't be documented in the AsyncAPI documentation. This might be acceptable for sending occasional one-off messages. However, if you're building a comprehensive service, it's recommended to create publisher objects. These objects can then be parsed and documented in your service's AsyncAPI documentation. Let's go ahead and create those publisher objects!

1. Create your KafkaBroker instance

```python linenums="1"
broker = KafkaBroker("localhost:9092")
```

2. Create a publisher instance

```python linenums="1"
prepared_publisher = broker.publisher("input_data")
```

2. Publish a message using the `publish` method of the prepared publisher

```python linenums="1"
        msg = Data(data=0.5)

        await prepared_publisher.publish(
            model_to_json(msg),
            headers={"content-type": "application/json"},
        )
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

1. **Initialize the KafkaBroker instance:** Start by initializing a KafkaBroker instance with the necessary configuration, including Kafka broker address.

```python linenums="1"
broker = KafkaBroker("localhost:9092")
```

2. **Prepare your publisher object to use later as a decorator:**

```python linenums="1"
to_output_data = broker.publisher("output_data")
```

3. **Create your processing logic:** Write a function that will consume the incoming messages in the defined format and produce a response to the defined topic

```python linenums="1"
async def on_input_data(msg: Data) -> Data:
    return Data(data=msg.data + 1.0)
```

4. **Decorate your processing function:** To connect your processing function to the desired Kafka topics you need to decorate it with `#!python @broker.subscriber` and `#!python @broker.publisher` decorators. Now, after you start your application, your processing function will be called whenever a new message in the subscribed topic is available and produce the function return value to the topic defined in the publisher decorator.

```python linenums="1"
@to_output_data
@broker.subscriber("input_data")
async def on_input_data(msg: Data) -> Data:
    return Data(data=msg.data + 1.0)
```
