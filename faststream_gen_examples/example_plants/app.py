from pydantic import BaseModel, Field, NonNegativeInt

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Plant(BaseModel):
    plant_id: NonNegativeInt = Field(..., examples=[1], description="Int data example")
    species: str = Field(..., examples=["Apple"], description="Species example")
    ready_to_sell: bool


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_sell_plant = broker.publisher("sell_plant")
to_still_growing = broker.publisher("still_growing")


@broker.subscriber("plant_growth")
async def on_plant_growth(msg: Plant, logger: Logger) -> None:
    logger.info(msg)

    if msg.ready_to_sell:
        await to_sell_plant.publish(msg.plant_id)
    else:
        await to_still_growing.publish(msg.plant_id)
