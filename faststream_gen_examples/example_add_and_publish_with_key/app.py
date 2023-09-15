from typing import List

from pydantic import BaseModel, Field

from faststream import Context, ContextRepo, FastStream, Logger
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


@app.on_startup
async def app_setup(context: ContextRepo):
    message_history: List[Point] = []
    context.set_global("message_history", message_history)


@broker.subscriber("input_data")
async def on_input_data(
    msg: Point,
    logger: Logger,
    context: ContextRepo,
    key: bytes = Context("message.raw_message.key"),
) -> None:
    logger.info(f"{msg=}")

    message_history = context.get("message_history")
    message_history.append(msg)
    context.set_global("message_history", message_history)

    x_sum = 0
    y_sum = 0
    for msg in message_history:
        x_sum += msg.x
        y_sum += msg.y

    point_sum = Point(x=x_sum, y=y_sum)
    await to_output_data.publish(point_sum, key=key)
