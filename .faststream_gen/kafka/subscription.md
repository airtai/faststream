# Basic Subscriber

To start consuming from a Kafka topic just decorate your consuming function with a `@broker.subscriber(...)` decorator passing a string as a topic key.

In the folowing example we will create a simple FastStream app that will consume `HelloWorld` messages from a **hello_world** topic.

The full app code looks like this:

```python
from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class HelloWorld(BaseModel):
    msg: str = Field(
        ...,
        examples=["Hello"],
        description="Demo hello world message",
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("hello_world")
async def on_hello_world(msg: HelloWorld, logger: Logger):
    logger.info(msg)
```
