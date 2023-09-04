from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_decrement_data = broker.publisher("decrement_data")
to_increment_data = broker.publisher("increment_data")


@broker.subscriber("input_data")
async def on_input_data(msg: Data, logger: Logger):
    logger.info(f"Consuming: {msg}")

    await to_increment_data.publish(Data(data=msg.data * 2.0))

    await to_decrement_data.publish(Data(data=msg.data * 0.5))
