# Batch publishing

If you want to send your data in batches `broker.publisher` makes that possible for you. By returning a tuple of messages you want to send in a batch the publisher will collect the messages and send them in a batch to a Kafka broker.

This guide will demonstrate how to use this feature.

## Return a batch from the publishing function

To define a batch that you want to produce to Kafka topic, you need to set the `batch` parameter of the publisher to `True` and return a tuple of messages that you want to send in a batch.

``` python hl_lines="1 7-10"
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class DataBasic(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )

# Code below omitted 👇
```

<details>
<summary>👀 Full file preview</summary>

``` python
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class DataBasic(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("output_data")
@broker.subscriber("input_data")
async def on_input_data(msg: DataBasic, logger: Logger) -> DataBasic:
    logger.info(msg)
    return DataBasic(data=msg.data + 1.0)
```

</details>
