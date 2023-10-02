# Using a Partition Key

Partition keys are a crucial concept in Apache Kafka, enabling you to determine the appropriate partition for a message. This ensures that related messages are kept together in the same partition, which can be invaluable for maintaining order or grouping related messages for efficient processing. Additionally, Kafka utilizes partitioning to distribute load across multiple brokers and scale horizontally, while replicating data across brokers provides fault tolerance.

You can specify your partition keys when utilizing the `@KafkaBroker.publisher(...)` decorator in FastStream. This guide will walk you through the process of using partition keys effectively.

## Publishing with a Partition Key

To publish a message to a Kafka topic using a partition key, follow these steps:

### Step 1: Define the Publisher

In your FastStream application, define the publisher using the `@KafkaBroker.publisher(...)` decorator. This decorator allows you to configure various aspects of message publishing, including the partition key.

```python linenums="1"
to_output_data = broker.publisher("output_data")
```

### Step 2: Pass the Key

When you're ready to publish a message with a specific key, simply include the `key` parameter in the `publish` function call. This key parameter is used to determine the appropriate partition for the message.

```python linenums="1"
    await to_output_data.publish(Data(data=msg.data + 1.0), key=b"key")
```

## Example Application

Let's examine a complete application example that consumes messages from the **input_data** topic and publishes them with a specified key to the **output_data** topic. This example will illustrate how to incorporate partition keys into your Kafka-based applications:

```python linenums="1"
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import Context, FastStream, Logger
from faststream.kafka import KafkaBroker


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


to_output_data = broker.publisher("output_data")


@broker.subscriber("input_data")
async def on_input_data(
    msg: Data, logger: Logger, key: bytes = Context("message.raw_message.key")
) -> None:
    logger.info(f"on_input_data({msg=})")
    await to_output_data.publish(Data(data=msg.data + 1.0), key=b"key")
```

As you can see, the primary difference from standard publishing is the inclusion of the `key` parameter in the `publish` call. This key parameter is essential for controlling how Kafka partitions and processes your messages.

In summary, using partition keys in Apache Kafka is a fundamental practice for optimizing message distribution, maintaining order, and achieving efficient processing. It is a key technique for ensuring that your Kafka-based applications scale gracefully and handle large volumes of data effectively.
