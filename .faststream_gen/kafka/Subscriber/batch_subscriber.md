# Batch Subscriber

If you want to consume data in batches, the `@broker.subscriber(...)` decorator makes it possible. By defining your consumed `msg` object as a list of messages and setting the `batch` parameter to `True`, the subscriber will call your consuming function with a batch of messages consumed from a single partition. Let's walk through how to achieve this.

## Using the Subscriber with Batching

To consume messages in batches, follow these steps:

### Step 1: Define Your Subscriber

In your FastStream application, define the subscriber using the `@broker.subscriber(...)` decorator. Ensure that you configure the `msg` object as a list and set the `batch` parameter to `True`. This configuration tells the subscriber to handle message consumption in batches.

```python linenums="1"
@broker.subscriber("test_batch", batch=True)
```

### Step 2: Implement Your Consuming Function

Create a consuming function that accepts the list of messages. The `@broker.subscriber(...)` decorator will take care of collecting and grouping messages into batches based on the partition.

```python linenums="1"
@broker.subscriber("test_batch", batch=True)
async def handle_batch(msg: List[HelloWorld], logger: Logger):
    logger.info(msg)
```

## Example of Consuming in Batches

Let's illustrate how to consume messages in batches from the **test_batch** topic with a practical example:

```python linenums="1"
from typing import List

from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


class HelloWorld(BaseModel):
    msg: str = Field(
        ...,
        examples=["Hello"],
        description="Demo hello world message",
    )


@broker.subscriber("test_batch", batch=True)
async def handle_batch(msg: List[HelloWorld], logger: Logger):
    logger.info(msg)
```

In this example, the subscriber is configured to process messages in batches, and the consuming function is designed to handle these batches efficiently.

Consuming messages in batches is a valuable technique when you need to optimize the processing of high volumes of data in your Kafka-based applications. It allows for more efficient resource utilization and can enhance the overall performance of your data pipelines.
