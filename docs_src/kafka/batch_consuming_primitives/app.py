from typing import List
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

@broker.subscriber("hello_world", batch=True)
async def on_hello_world(msg: List[str], logger: Logger):
    logger.info(msg)
