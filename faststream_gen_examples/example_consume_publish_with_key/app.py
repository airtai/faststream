from pydantic import BaseModel, Field

from faststream import Context, FastStream, Logger
from faststream.kafka import KafkaBroker


class Point(BaseModel):
    x: float = Field(
        ..., examples=[0.5], description="The X Coordinate in the coordinate system"
    )
    y: float = Field(
        ..., examples=[0.5], description="The Y Coordinate in the coordinate system"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


to_output_data = broker.publisher("output_data")


@broker.subscriber("input_data")
async def on_input_data(
    msg: Point, logger: Logger, key: bytes = Context("message.raw_message.key")
) -> None:
    logger.info(f"{msg=}")
    incremented_point = Point(x=msg.x + 1, y=msg.y + 1)
    await to_output_data.publish(incremented_point, key=key)
