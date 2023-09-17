# Publishing in batches

If you want to send your data in batches `@publisher` decorator makes that possible for you.
To produce in batches you need to do two things:

1. When creating your publisher, set the `batch` argument to `True`
2. Return a tuple of the messages you wish to send in a batch. This action will prompt the producer to collect the messages and send them in a batch to a Kafka broker.


Here is an example of an app producing in batches to **output_data** topic when consuming from **input_data_1**.

In the highligted lines, we can see the steps of creating and using a batch publisher:

1. Creation of publisher
2. Publishing an actual batch of messages

```python hl_lines="19 26"
from typing import Tuple

from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


decrease_and_increase = broker.publisher("output_data", batch=True)


@decrease_and_increase
@broker.subscriber("input_data_1")
async def on_input_data_1(msg: Data, logger: Logger) -> Tuple[Data, Data]:
    logger.info(msg)
    return Data(data=(msg.data * 0.5)), Data(data=(msg.data * 2.0))
```
