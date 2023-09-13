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
    """
    Processes a message from the 'plant_growth' topic.
    Upon reception, the function should verify if the ready_to_sell attribute is True.
    If yes, publish plant_id to the 'sell_plant' topic, otherwise, publish plant_id to the 'still_growing' topic.

    Instructions:
    1. Consume a message from 'plant_growth' topic.
    2. Check if the ready_to_sell attribute is True.
    3. If ready_to_sell is True, publish plant_id to the 'sell_plant' topic, otherwise, publish plant_id to the 'still_growing' topic.

    """
    raise NotImplementedError()
