# Defining a partition key

Partition keys are used in Apache Kafka to determine which partition a message should be written to. This ensures that related messages are kept together in the same partition, which can be useful for ensuring order or for grouping related messages together for efficient processing. Additionally, partitioning data across multiple partitions allows Kafka to distribute load across multiple brokers and scale horizontally, while replicating data across multiple brokers provides fault tolerance.

You can define your partition keys when using the `#!python @KafkaBroker.publisher(...)`, this guide will demonstrate to you this feature.

## Calling `publish` with a key

To publish a message to a Kafka topic using a key, simpliy pass the `key` parameter to the `publish` function call, like this:

```python linenums="1"
    await to_output_data.publish(Data(data=msg.data + 1.0), key=b"key")
```

## App example

Lest take a look at the whole app example that will consume from the **input_data** topic and publish with key to the **output_data** topic.

You can see that the only difference from normal publishing is that now we pass the key to the publisher call.

```python linenums="1" hl_lines="25"
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
