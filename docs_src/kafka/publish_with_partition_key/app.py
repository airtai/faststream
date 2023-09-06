from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


to_output_data = broker.publisher("output_data")


@broker.subscriber("input_data")
# we should be able to get the key (and other stuff like partion, offset, etc injected)
async def on_input_data(msg: Data, logger: Logger, key: bytes) -> None:
    logger.info(f"on_input_data({msg=})")
    await to_output_data.publish(Data(data=msg.data + 1.0), key=b"key")


@broker.subscriber("output_data")
async def on_output_data(msg: Data, logger: Logger, key: bytes) -> None:
    logger.info(f"on_output_data({msg=})")
